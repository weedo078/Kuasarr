# -*- coding: utf-8 -*-
# Quasarr
# Project by https://github.com/rix1337

import base64
import json
import os
import pickle

import requests

from quasarr.providers.log import info, debug


def create_and_persist_session(shared_state):
    """Create a new DL session with cookie authentication."""
    hostname = shared_state.values["config"]("Hostnames").get("dl")
    if not hostname:
        debug("DL hostname not configured")
        return None
    
    dl_session = requests.Session()
    
    # Define cookie file paths
    cookie_paths = [
        "/app/dl_cookies.json",
        "/config/dl_cookies.json", 
        "dl_cookies.json"
    ]
    
    cookies_loaded = False
    for cookie_path in cookie_paths:
        if os.path.exists(cookie_path):
            try:
                with open(cookie_path, 'r') as f:
                    cookies_data = json.load(f)
                
                debug(f"Loading cookies from {cookie_path}")
                
                # Handle different cookie file formats
                if isinstance(cookies_data, list):
                    for cookie in cookies_data:
                        if cookie.get('domain') and hostname.strip().lower() in cookie['domain'].lower():
                            dl_session.cookies.set(
                                cookie['name'], 
                                cookie['value'], 
                                domain=cookie['domain'],
                                path=cookie.get('path', '/'),
                                secure=cookie.get('secure', False)
                            )
                            cookies_loaded = True
                
                elif 'cookie_details' in cookies_data:
                    cookie_details = cookies_data['cookie_details']
                    for name, details in cookie_details.items():
                        if details.get('domain') and hostname.strip().lower() in details['domain'].lower():
                            dl_session.cookies.set(
                                name,
                                details['value'],
                                domain=details['domain'],
                                path=details.get('path', '/'),
                                secure=details.get('secure', False)
                            )
                            cookies_loaded = True
                
                elif 'cookies' in cookies_data:
                    simple_cookies = cookies_data['cookies']
                    
                    for name, value in simple_cookies.items():
                        # Versuche die echte Domain aus cookie_details zu bekommen
                        domain_to_use = f"www.{hostname.strip()}"
                        path_to_use = '/'
                        secure_to_use = True
                        
                        if 'cookie_details' in cookies_data and name in cookies_data['cookie_details']:
                            details = cookies_data['cookie_details'][name]
                            domain_to_use = details.get('domain', domain_to_use)
                            path_to_use = details.get('path', path_to_use)
                            secure_to_use = details.get('secure', secure_to_use)
                        
                        dl_session.cookies.set(
                            name,
                            value,
                            domain=domain_to_use,
                            path=path_to_use,
                            secure=secure_to_use
                        )
                        cookies_loaded = True
                
                if cookies_loaded:
                    debug(f"Successfully loaded cookies from {cookie_path}")
                    break
                    
            except Exception as e:
                debug(f"Failed to load cookies from {cookie_path}: {e}")
                continue
        
    if not cookies_loaded:
        debug("No valid cookie file found for DL")
        return None
    
    # Validate the session
    if validate_session(dl_session, shared_state.values["config"]):
        # Persist the session to database
        serialized_session = pickle.dumps(dl_session)
        session_string = base64.b64encode(serialized_session).decode('utf-8')
        shared_state.values["database"]("sessions").update_store("dl", session_string)
        info(f"DL session created and persisted for {hostname}")
        return dl_session
    else:
        debug("DL session validation failed")
        return None


def retrieve_and_validate_session(shared_state):
    """Retrieve and validate existing DL session from database."""
    session_string = shared_state.values["database"]("sessions").retrieve("dl")
    if not session_string:
        debug("No existing DL session found, creating new one")
        return create_and_persist_session(shared_state)
    
    try:
        serialized_session = base64.b64decode(session_string.encode('utf-8'))
        dl_session = pickle.loads(serialized_session)
        if not isinstance(dl_session, requests.Session):
            raise ValueError("Retrieved object is not a valid requests.Session instance.")
        
        # Validate the session
        hostname = shared_state.values["config"]("Hostnames").get("dl")
        if validate_session(dl_session, shared_state.values["config"]):
            debug("Retrieved DL session is valid")
            return dl_session
        else:
            debug("Retrieved DL session is invalid, creating new one")
            return create_and_persist_session(shared_state)
            
    except Exception as e:
        debug(f"DL session retrieval failed: {e}")
        return create_and_persist_session(shared_state)


def validate_session(session, config):
    """
    Validiert eine DL-Session durch Prüfung einer echten Thread-Seite
    """
    try:
        # Teste zuerst Account-Zugang
        account_url = "https://www.data-load.me/account/"
        account_response = session.get(account_url, timeout=30)
        
        print(f"[DL-VALIDATION] Account-Seite Status: {account_response.status_code}")
        print(f"[DL-VALIDATION] Account-Seite Cookies: {len(session.cookies)} cookies")
        
        # Debug: Zeige alle Cookie-Namen
        cookie_names = [cookie.name for cookie in session.cookies]
        print(f"[DL-VALIDATION] Cookie-Namen: {cookie_names}")
        
        # Teste dann Thread-Zugang mit einem echten Thread
        # Verwende einen bekannten Thread für Better Call Saul
        thread_url = "https://www.data-load.me/threads/better-call-saul-s01-2015-german-dl-1080p-bluray-x264-euhdtv.23549/"
        thread_response = session.get(thread_url, timeout=30)
        
        print(f"[DL-VALIDATION] Thread-Seite Status: {thread_response.status_code}")
        print(f"[DL-VALIDATION] Thread-Seite Content-Length: {len(thread_response.text)}")
        
        # Eindeutige Login-erforderlich Indikatoren
        login_indicators = [
            'Sie müssen sich registrieren',   # Registrierungs-Text
            'Anmelden oder registrieren',     # Anmelde-Text
            'Log in or register',             # Englischer Login-Text
            'Du musst dich einloggen',        # Alternative Login-Meldung
            'data-logged-in="false"'          # XenForo logged-out Status
        ]
        
        # Erfolgreiche Login-Indikatoren
        success_indicators = [
            'data-logged-in="true"',          # XenForo logged-in Status
            'xf_user',                        # User-Cookie im HTML
        ]
        
        download_indicators = [
            'keeplinks.org',                  # Container-Links
            'filecrypt.cc',                   # FileCrypt-Links
            'turbobit.net',                   # Direct-Downloads
            'rapidgator.net',                 # Premium-Hoster
            'nitroflare.com'                  # Weitere Hoster
        ]
        
        # Prüfe auf Login-Indikatoren
        login_found = []
        for indicator in login_indicators:
            if indicator in thread_response.text:
                login_found.append(indicator)
        
        # Prüfe auf Erfolgs-Indikatoren
        success_found = []
        for indicator in success_indicators:
            if indicator in thread_response.text:
                success_found.append(indicator)
        
        # Prüfe auf Download-Indikatoren
        download_found = []
        for indicator in download_indicators:
            if indicator in thread_response.text:
                download_found.append(indicator)
        
        print(f"[DL-VALIDATION] Login-erforderlich Indikatoren: {login_found}")
        print(f"[DL-VALIDATION] Erfolgreiche Login-Indikatoren: {success_found}")
        print(f"[DL-VALIDATION] Download-Indikatoren gefunden: {download_found}")
        
        # Debug: Speichere einen Teil der Thread-Seite für Analyse
        thread_sample = thread_response.text[:2000].replace('\n', ' ').replace('\r', '')
        print(f"[DL-VALIDATION] Thread-Seite Anfang: {thread_sample[:500]}...")
        
        # Neue Validierungslogik: Erfolg wenn logged-in UND downloads vorhanden
        if login_found:
            print(f"[DL-VALIDATION] Thread-Zugang fehlgeschlagen - Login erforderlich")
            return False
        
        if success_found and download_found:
            print(f"[DL-VALIDATION] Thread-Zugang erfolgreich - Eingeloggt UND Download-Links vorhanden")
            return True
        
        if success_found:
            print(f"[DL-VALIDATION] Thread-Zugang erfolgreich - Eingeloggt (Downloads optional)")
            return True
        
        # Fallback: Wenn keine eindeutigen Indikatoren
        print(f"[DL-VALIDATION] Thread-Zugang unklar - keine eindeutigen Indikatoren")
        return False  # Vorsichtiger: bei Unklarheit als ungültig betrachten
        
    except Exception as e:
        print(f"[DL-VALIDATION] Validierungsfehler: {e}")
        return False


def invalidate_session(shared_state):
    """Invalidate the current DL session."""
    db = shared_state.values["database"]("sessions")
    db.delete("dl")
    debug('DL session marked as invalid!') 