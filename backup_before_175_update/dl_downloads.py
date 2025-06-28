# -*- coding: utf-8 -*-
# Quasarr
# Project by https://github.com/rix1337

import re
import time
from urllib.parse import quote_plus, unquote_plus
import random
import json

import requests
from bs4 import BeautifulSoup

from quasarr.providers.log import info, debug

import hashlib
from base64 import urlsafe_b64encode

# Hash für sicheren Hostname-Check (sha256 von "data-load.me")
DL_HOSTNAME_HASH = "e250f2750bcb7d82"

# Globale Session-Verwaltung
_dl_session = None
_dl_session_valid = False
_dl_hostname = None

def validate_hostname_hash(hostname):
    """Prüft ob der Hostname dem erwarteten Hash entspricht"""
    if not hostname:
        return False
    
    hostname_hash = hashlib.sha256(hostname.encode()).hexdigest()[:16]
    return hostname_hash == DL_HOSTNAME_HASH

def try_cookie_session(shared_state, hostname):
    """
    Versucht eine Session mit importierten Browser-Cookies zu erstellen
    """
    global _dl_session, _dl_session_valid
    
    try:
        from os import environ
        import json
        import os
        from datetime import datetime
        
        # Prüfe Cookie-Pfad aus Umgebungsvariable oder Config
        cookie_sources = [
            environ.get("DL_COOKIES", "").strip(),
            shared_state.values.get("config", lambda x: {}).get("DL", {}).get("cookies", ""),
            "/config/dl_cookies.json",  # Standard Docker-Pfad
            "dl_cookies.json"  # Lokaler Pfad
        ]
        
        cookie_file = None
        for source in cookie_sources:
            if source and os.path.exists(source):
                cookie_file = source
                break
        
        if not cookie_file:
            debug("[DL-COOKIES] Keine Cookie-Datei gefunden")
            return False
        
        debug(f"[DL-COOKIES] Lade Cookies aus: {cookie_file}")
        
        # Lade Cookie-Daten
        with open(cookie_file, 'r', encoding='utf-8') as f:
            cookie_data = json.load(f)
        
        # Extrahiere Session-Cookies
        if 'cookies' not in cookie_data:
            debug("[DL-COOKIES] Ungültiges Cookie-Format")
            return False
        
        session_cookies = cookie_data['cookies']
        debug(f"[DL-COOKIES] {len(session_cookies)} Cookies geladen")
        
        # Erstelle Session mit Cookies
        session = requests.Session()
        session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7',
                'Connection': 'keep-alive',
        })
        
        # Setze Cookies in Session
        for name, value in session_cookies.items():
            session.cookies.set(name, value, domain=hostname.strip())
        
        # Validiere Cookie-Session
        if validate_session(session, hostname):
            _dl_session = session
            _dl_session_valid = True
            debug(f"[DL-COOKIES] ✅ Cookie-Session erfolgreich validiert")
            
            # Optional: Cookie-Metadaten loggen
            if 'metadata' in cookie_data:
                metadata = cookie_data['metadata']
                debug(f"[DL-COOKIES] Cookie-Metadaten: {metadata.get('extracted_at', 'unbekannt')}")
            
            return True
        else:
            debug("[DL-COOKIES] ❌ Cookie-Session ungültig - Cookies möglicherweise abgelaufen")
            return False
            
    except Exception as e:
        debug(f"[DL-COOKIES] Fehler beim Cookie-Import: {e}")
        return False

def save_session_cookies(session, shared_state):
    """
    Speichert Session-Cookies für zukünftige Verwendung
    """
    try:
        from os import environ
        import json
        import os
        from datetime import datetime
        
        cookie_file = environ.get("DL_COOKIES", "/config/dl_cookies.json")
        
        # Extrahiere Cookies aus Session
        session_cookies = {}
        for cookie in session.cookies:
            if 'data-load.me' in cookie.domain:
                session_cookies[cookie.name] = cookie.value
        
        if not session_cookies:
            return False
        
        # Erstelle Cookie-Daten
        cookie_data = {
            'cookies': session_cookies,
            'metadata': {
                'domain': 'data-load.me',
                'extracted_at': datetime.now().isoformat(),
                'total_cookies': len(session_cookies),
                'source': 'quasarr_session'
            }
        }
        
        # Speichere Cookies
        with open(cookie_file, 'w', encoding='utf-8') as f:
            json.dump(cookie_data, f, indent=2, ensure_ascii=False)
        
        debug(f"[DL-COOKIES] Session-Cookies gespeichert: {cookie_file}")
        return True
        
        except Exception as e:
        debug(f"[DL-COOKIES] Fehler beim Speichern: {e}")
        return False

def initialize_dl_session(shared_state):
    """
    Initialisiert die DL-Session beim Container-Start
    Versucht erst Cookie-Import, dann Credentials als Fallback
    """
    global _dl_session, _dl_session_valid, _dl_hostname
    
    # Reset bei neuer Initialisierung
    _dl_session = None
    _dl_session_valid = False
    _dl_hostname = None
    
    # Prüfe Hostname-Konfiguration
    hostname = shared_state.values["config"]("Hostnames").get("dl")
    if not hostname or not validate_hostname_hash(hostname):
        debug("[DL-INIT] Hostname nicht konfiguriert oder ungültig")
        return False
    
    _dl_hostname = hostname
    
    # Strategie 1: Cookie-Import versuchen
    if try_cookie_session(shared_state, hostname):
        debug("[DL-INIT] ✅ Session via Cookie-Import erfolgreich erstellt")
        return True
    
    # Strategie 2: Credentials-Login als Fallback
    from os import environ
    dl_user = environ.get("DL_USER", "").strip()
    dl_password = environ.get("DL_PASSWORD", "").strip()
    
    if not dl_user or not dl_password:
        debug("[DL-INIT] Weder Cookies noch Credentials verfügbar - Session wird bei Bedarf erstellt")
        return False
    
    debug(f"[DL-INIT] Cookie-Import fehlgeschlagen - versuche Credentials-Login für {dl_user}")
    
    try:
        # Erstelle Session mit Login
        session = requests.Session()
        session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        })
        
        # Login-Prozess - versuche verschiedene URLs (mit URL-Bereinigung)
        login_urls = [
            f"https://{hostname.strip()}/login/",
            f"https://{hostname.strip()}/login/login",
            f"https://{hostname.strip()}/login"
        ]
        
        login_success = False
        for login_url in login_urls:
            try:
                debug(f"[DL-INIT] Versuche Login-Seite: {login_url}")
                
                login_page = session.get(login_url, timeout=15)
                if login_page.status_code != 200:
                    debug(f"[DL-INIT] Login-Seite nicht erreichbar (Status: {login_page.status_code})")
                    continue
                
                soup = BeautifulSoup(login_page.text, 'html.parser')
                
                # Verschiedene Strategien zur Formular-Suche
        login_form = None
        
                # Strategie 1: Form mit action="login"
                login_form = soup.find('form', action=re.compile(r'login'))
                
                # Strategie 2: Form mit login-spezifischen Feldern
                if not login_form:
                    forms = soup.find_all('form')
                    for form in forms:
                        if form.find('input', {'name': re.compile(r'(login|username|email)', re.I)}) and \
                           form.find('input', {'name': re.compile(r'password', re.I)}):
                login_form = form
                break
        
                # Strategie 3: Erstes verfügbares Formular mit Passwort-Feld
        if not login_form:
                    forms = soup.find_all('form')
                    for form in forms:
                        if form.find('input', {'type': 'password'}):
                    login_form = form
                    break
        
        if not login_form:
                    debug(f"[DL-INIT] Kein Login-Formular auf {login_url} gefunden")
                continue
                
                debug(f"[DL-INIT] Login-Formular gefunden")
                
                # Sammle Formular-Daten
                form_data = {}
                for input_field in login_form.find_all('input'):
                    name = input_field.get('name', '')
                    value = input_field.get('value', '')
                    input_type = input_field.get('type', 'text')
                    
                    # Setze Login-Credentials - verschiedene Feldnamen
                    if name and name.lower() in ['login', 'username', 'email', 'user']:
                        value = dl_user
                    elif name and name.lower() == 'password':
                        value = dl_password
                    elif input_type == 'checkbox':
                        # Aktiviere alle Checkboxen (wichtig für XenForo)
                        value = '1'
                    elif input_type == 'hidden':
                        # Behalte versteckte Felder (CSRF-Token etc.)
                        pass
                    
                    # Speichere Feld - auch wenn Name leer ist
                    if name or input_type in ['checkbox', 'hidden']:
                        if not name:
                            # Generiere einen Namen für namenlose Felder
                            name = f"unnamed_{input_type}_{len(form_data)}"
                        form_data[name] = value
                
                debug(f"[DL-INIT] Formular-Daten: {list(form_data.keys())}")
                
                # Login-Request
                form_action = login_form.get('action', '')
                if form_action.startswith('http'):
                    login_submit_url = form_action
                elif form_action.startswith('/'):
                    login_submit_url = f"https://{hostname.strip()}{form_action.strip()}"
                else:
                    login_submit_url = f"{login_url.strip().rstrip('/')}/{form_action.strip()}" if form_action else login_url.strip()
                
                debug(f"[DL-INIT] Sende Login-Request an: {login_submit_url}")
                
                # Zusätzliche Header für Login
        session.headers.update({
                    'Referer': login_url.strip(),
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Origin': f"https://{hostname.strip()}"
                })
                
                login_response = session.post(login_submit_url, data=form_data, timeout=15, allow_redirects=True)
                
                debug(f"[DL-INIT] Login-Response Status: {login_response.status_code}")
                debug(f"[DL-INIT] Login-Response URL: {login_response.url}")
                
                if login_response.status_code == 200:
                    login_success = True
                    break
                else:
                    debug(f"[DL-INIT] Login fehlgeschlagen mit Status {login_response.status_code}")
                    
            except Exception as e:
                debug(f"[DL-INIT] Fehler bei Login-URL {login_url}: {e}")
                continue
        
        if not login_success:
            debug("[DL-INIT] Alle Login-Versuche fehlgeschlagen")
            return False
        
        # Validiere Login
        if validate_session(session, hostname):
            _dl_session = session
            _dl_session_valid = True
            debug(f"[DL-INIT] ✅ Session erfolgreich erstellt für {dl_user}")
            
            # Optional: Speichere erfolgreiche Session-Cookies für zukünftige Verwendung
            save_session_cookies(session, shared_state)
            
            return True
        else:
            debug(f"[DL-INIT] ❌ Login fehlgeschlagen für {dl_user}")
            return False
            
    except Exception as e:
        debug(f"[DL-INIT] Fehler beim Session-Setup: {e}")
        return False

def validate_session(session, hostname):
    """Prüft ob eine Session gültig/eingeloggt ist"""
    try:
        test_url = f"https://{hostname.strip()}/account/"
        response = session.get(test_url, timeout=10)
        response.raise_for_status()
        
        # Prüfe auf Login-Indikatoren
        content = response.text.lower()
        
        # Positive Indikatoren (eingeloggt)
        logged_in_indicators = [
            "logout", "abmelden", "account", "profil", 
            "benutzerkontrollzentrum", "user-info", "member-header",
            "account-wrapper", "account-content"
        ]
        
        # Negative Indikatoren (nicht eingeloggt)  
        logged_out_indicators = [
            "please log in", "bitte anmelden", "login required",
            "you must be logged", "anmeldung erforderlich"
        ]
        
        # Prüfe negative Indikatoren zuerst
        for indicator in logged_out_indicators:
            if indicator in content:
                return False
        
        # Prüfe positive Indikatoren
        for indicator in logged_in_indicators:
            if indicator in content:
                return True
        
        # Fallback: Prüfe ob Account-spezifische Elemente vorhanden sind
        soup = BeautifulSoup(response.text, 'html.parser')
        account_elements = soup.find_all(['a', 'div', 'span'], text=re.compile(r'(logout|abmelden|profil|account)', re.IGNORECASE))
        
        return len(account_elements) > 0
        
    except Exception as e:
        debug(f"Session-Validierung fehlgeschlagen: {e}")
        return False

def get_persistent_session(shared_state):
    """
    Liefert die persistente DL-Session zurück
    Falls keine Session vorhanden, wird versucht eine zu erstellen
    """
    global _dl_session, _dl_session_valid, _dl_hostname
    
    # Prüfe ob Session bereits vorhanden und gültig
    if _dl_session and _dl_session_valid:
        # Gelegentliche Re-Validierung (alle ~100 Anfragen)
        if random.randint(1, 100) == 1:
            if not validate_session(_dl_session, _dl_hostname):
                debug("[DL-SESSION] Session ungültig geworden - versuche Erneuerung")
                _dl_session_valid = False
                return initialize_and_get_session(shared_state)
        
        return _dl_session
    
    # Keine gültige Session vorhanden - versuche Initialisierung
    return initialize_and_get_session(shared_state)

def initialize_and_get_session(shared_state):
    """Initialisiert eine neue Session und gibt sie zurück"""
    global _dl_session, _dl_session_valid
    
    if initialize_dl_session(shared_state):
        return _dl_session
    else:
        # Fallback: Erstelle anonyme Session für nicht-geschützte Inhalte
        debug("[DL-SESSION] Erstelle anonyme Session für öffentliche Inhalte")
        
        anonymous_session = requests.Session()
        anonymous_session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7',
        'Connection': 'keep-alive',
        })
        
        return anonymous_session

def startup_initialize_session(shared_state):
    """
    Wird beim Container-Start aufgerufen um Session zu initialisieren
    """
    debug("[DL-STARTUP] Prüfe DL-Session-Initialisierung...")
    
    hostname = shared_state.values["config"]("Hostnames").get("dl")
    if not hostname:
        debug("[DL-STARTUP] Kein DL-Hostname konfiguriert")
        return
    
    if not validate_hostname_hash(hostname):
        debug("[DL-STARTUP] Ungültiger DL-Hostname konfiguriert") 
        return
    
    from os import environ
    
    # Prüfe zuerst auf Cookie-Konfiguration
    dl_cookies = environ.get("DL_COOKIES", "").strip()
    if dl_cookies:
        debug(f"[DL-STARTUP] Cookie-Konfiguration gefunden: {dl_cookies}")
        debug("[DL-STARTUP] Versuche Cookie-Session-Initialisierung...")
        success = initialize_dl_session(shared_state)
        if success:
            debug("[DL-STARTUP] ✅ DL-Session erfolgreich mit Cookies initialisiert")
            return
        else:
            debug("[DL-STARTUP] ⚠️ Cookie-Session-Initialisierung fehlgeschlagen")
    
    # Fallback auf Credentials
    dl_user = environ.get("DL_USER", "").strip()
    dl_password = environ.get("DL_PASSWORD", "").strip()
    
    if dl_user and dl_password:
        debug(f"[DL-STARTUP] Credentials gefunden für {dl_user} - initialisiere Session...")
        success = initialize_dl_session(shared_state)
        if success:
            debug("[DL-STARTUP] ✅ DL-Session erfolgreich mit Credentials initialisiert")
        else:
            debug("[DL-STARTUP] ❌ Credentials-Session-Initialisierung fehlgeschlagen")
    else:
        if not dl_cookies:
            debug("[DL-STARTUP] Weder Cookies noch Credentials gefunden - Session wird bei Bedarf erstellt")
        else:
            debug("[DL-STARTUP] Session wird bei Bedarf erstellt")

def clean_cookies(session):
    """Entfernt doppelte Cookies aus einer Session"""
    debug("Bereinige Cookies...")
    
    # Cookie Jar extrahieren
    jar = session.cookies._cookies
    
    # Für jede Domain
    for domain in list(jar.keys()):
        for path in list(jar[domain].keys()):
            # Für jeden Cookie-Namen
            seen_cookies = set()
            for name in list(jar[domain][path].keys()):
                # Wenn wir diesen Cookie-Namen bereits gesehen haben
                if name in seen_cookies:
                    debug(f"Entferne doppelten Cookie: {name} für {domain}{path}")
                    del jar[domain][path][name]
                else:
                    seen_cookies.add(name)
    
    debug(f"Bereinigte Cookies: {dict(session.cookies)}")
    return session


def get_dl_download_link(shared_state, url):
    """Extrahiert den Download-Link aus der angegebenen URL"""
    dl = shared_state.values["config"]("Hostnames").get("dl")
    if not dl:
        debug("Hostname für DL nicht konfiguriert")
        return None
    
    # Prüfe, ob die URL zu data-load.me gehört
    if not url or dl not in url:
        debug(f"URL {url} ist keine gültige DL-URL")
        return None
    
    debug(f"========== GET_DL_DOWNLOAD_LINK START =========")
    debug(f"Versuche Download-Link aus URL zu extrahieren: {url}")
    
    # Session abrufen oder erstellen
    debug(f"Rufe Session ab oder erstelle eine neue...")
    session = get_persistent_session(shared_state)
    if not session:
        info("Konnte keine gültige DL-Session abrufen oder erstellen")
        debug(f"========== GET_DL_DOWNLOAD_LINK ENDE (keine Session) =========")
        return None
    
    try:
        # Verzögerung, um Erkennung als Bot zu vermeiden
        delay = random.uniform(0.5, 1.5)
        debug(f"Warte {delay:.2f} Sekunden vor dem Request...")
        time.sleep(delay)
        
        debug(f"Rufe URL ab: {url}")
        # Rufe die Thread-Seite ab
        response = session.get(url, timeout=10)
        debug(f"Response-Status: {response.status_code}")
        debug(f"Response-URL: {response.url}")
        debug(f"Response-Headers: {dict(response.headers)}")
        response.raise_for_status()
        
        # Überprüfe, ob wir angemeldet sind
        login_indicators = ["login", "anmelden", "registrieren"]
        logout_indicators = ["logout", "abmelden", "benutzerkontrollzentrum"]
        
        is_logged_in = any(indicator in response.text.lower() for indicator in logout_indicators)
        is_login_page = any(indicator in response.url.lower() for indicator in login_indicators) or \
                      (response.status_code == 200 and any(indicator in response.text.lower() for indicator in login_indicators) and \
                       not is_logged_in)
        
        debug(f"Login-Status: {'Eingeloggt' if is_logged_in else 'Nicht eingeloggt'}")
        debug(f"Ist Login-Seite: {'Ja' if is_login_page else 'Nein'}")
        
        # Rettungsversuch bei Weiterleitung zur Login-Seite
        if is_login_page:
            debug("Wurde zur Login-Seite weitergeleitet - neuer Login-Versuch...")
            session = get_persistent_session(shared_state)
            if not session:
                info("Erneuter Login-Versuch fehlgeschlagen")
                debug(f"========== GET_DL_DOWNLOAD_LINK ENDE (erneuter Login fehlgeschlagen) =========")
                return None
                
            # Versuche erneut, die Seite abzurufen
            debug(f"Versuche erneut, URL abzurufen: {url}")
            response = session.get(url, timeout=10)
            debug(f"Response-Status nach Login: {response.status_code}")
            debug(f"Response-URL nach Login: {response.url}")
            response.raise_for_status()
            
            # Prüfe, ob wir jetzt eingeloggt sind
            is_logged_in = any(indicator in response.text.lower() for indicator in logout_indicators)
            debug(f"Login-Status nach erneutem Login: {'Eingeloggt' if is_logged_in else 'Nicht eingeloggt'}")
            
            if not is_logged_in:
                info("Konnte nicht einloggen, selbst nach erneutem Versuch")
                debug(f"========== GET_DL_DOWNLOAD_LINK ENDE (Login fehlgeschlagen) =========")
                return None
        
        # Vollständiger HTML-Output für Debugging
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        thread_id = url.split('/')[-1].split('.')[0]
        html_file_path = f"debug_dl_page_{thread_id}_{timestamp}.html"
        
        try:
            with open(html_file_path, "w", encoding="utf-8") as f:
                f.write(response.text)
            debug(f"HTML-Seite für Debugging gespeichert unter: {html_file_path}")
        except Exception as e:
            debug(f"Konnte HTML-Datei nicht speichern: {e}")
            
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Extrahiere den Titel der Seite für Debugging
        page_title = soup.title.string if soup.title else "Kein Titel gefunden"
        debug(f"Seitentitel: {page_title}")
        
        # HTML-Struktur-Informationen
        header_count = len(soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']))
        div_count = len(soup.find_all('div'))
        a_count = len(soup.find_all('a'))
        form_count = len(soup.find_all('form'))
        script_count = len(soup.find_all('script'))
        
        debug(f"HTML-Struktur: {header_count} Überschriften, {div_count} Divs, {a_count} Links, {form_count} Formulare, {script_count} Scripts")
        
        # Suche nach Download-Links in der Seite
        download_links = []
        rapidgator_links = []
        
        # 1. ALLE LINKS AUSGEBEN
        debug("==== ALLE LINKS AUF DER SEITE ====")
        all_links = soup.find_all('a', href=True)
        
        link_stats = {
            'filecrypt': 0,
            'rapidgator': 0,
            'ddownload': 0,
            'other': 0
        }
        
        for a_tag in all_links:
            href = a_tag.get('href', '')
            text = a_tag.text.strip()
            
            if 'filecrypt.cc' in href:
                link_stats['filecrypt'] += 1
            elif 'rapidgator' in href or 'rapidgator' in text.lower():
                link_stats['rapidgator'] += 1
            elif 'ddownload' in href or 'ddownload' in text.lower():
                link_stats['ddownload'] += 1
            else:
                link_stats['other'] += 1
                
        debug(f"Link-Statistik: {link_stats}")
        
        # Links mit interessanten Attributen ausgeben
        interesting_links = []
        for i, a_tag in enumerate(all_links):
            href = a_tag.get('href', '')
            text = a_tag.text.strip()
            classes = a_tag.get('class', [])
            rel = a_tag.get('rel', [])
            target = a_tag.get('target', '')
            
            # Prüfe, ob der Link interessant ist
            is_interesting = (
                'filecrypt.cc' in href or
                'rapidgator' in href or 'rapidgator' in text.lower() or
                'ddownload' in href or 'ddownload' in text.lower() or
                'external' in classes or 
                'external' in rel or
                target == '_blank'
            )
            
            if is_interesting:
                interesting_links.append((href, text, classes, rel, target))
                debug(f"Interessanter Link {i}: href='{href}', text='{text}', class={classes}, rel={rel}, target='{target}'")
        
        debug(f"Anzahl interessanter Links: {len(interesting_links)}")
        
        # 2. STRUKTUR DER BEITRÄGE ANALYSIEREN
        debug("==== STRUKTUR DER BEITRÄGE ANALYSIEREN ====")
        
        # XenForo-spezifische Elemente
        message_bodies = soup.select('article.message-body')
        debug(f"Anzahl message-body Elemente: {len(message_bodies)}")
        
        bb_wrappers = soup.select('div.bbWrapper')
        debug(f"Anzahl bbWrapper Elemente: {len(bb_wrappers)}")
        
        blocks = soup.select('div.bbCodeBlock')
        debug(f"Anzahl bbCodeBlock Elemente: {len(blocks)}")
        
        spoilers = soup.select('div.bbCodeSpoiler')
        debug(f"Anzahl bbCodeSpoiler Elemente: {len(spoilers)}")
        
        # 3. SUCHE NACH FILECRYPT-LINKS MIT RAPIDGATOR IM TEXT
        debug("==== FILECRYPT.CC RAPIDGATOR LINKS ====")
        
        # Suche nach den filecrypt-Links mit "Rapidgator" im Text oder als Titel
        for a_tag in all_links:
            href = a_tag.get('href', '')
            text = a_tag.text.strip().lower()
            title = a_tag.get('title', '').lower()
            parent_text = ""
            
            # Versuche, den umgebenden Text zu extrahieren
            if a_tag.parent:
                parent_text = a_tag.parent.text.strip().lower()
            
            if 'filecrypt.cc' in href:
                is_rapidgator = ('rapidgator' in text or 'rapidgator' in title or 'rapidgator' in parent_text)
                debug(f"Filecrypt-Link gefunden: {href}")
                debug(f"  Text: '{text}'")
                debug(f"  Title: '{title}'")
                debug(f"  Umgebender Text: '{parent_text[:100]}...'")
                debug(f"  Ist Rapidgator-Link: {'Ja' if is_rapidgator else 'Nein'}")
                
                if is_rapidgator:
                    debug(f"Rapidgator-Link gefunden: {href}")
                    rapidgator_links.append(href)
        
        # 4. SUCHE IN SPEZIFISCHEN ELEMENTEN
        debug("==== SUCHE IN SPEZIFISCHEN ELEMENTEN ====")
        
        # Suche in bbWrapper-Elementen (Haupttext der Beiträge)
        if bb_wrappers and not rapidgator_links:
            debug("Suche in bbWrapper-Elementen...")
            
            for wrapper in bb_wrappers:
                wrapper_text = wrapper.get_text().lower()
                debug(f"bbWrapper Text (Auszug): {wrapper_text[:100]}...")
                
                # Prüfe, ob "rapidgator" im Text vorkommt
                if 'rapidgator' in wrapper_text:
                    debug("'rapidgator' in bbWrapper-Text gefunden")
                    
                    # Suche nach filecrypt.cc Links
                    for a_tag in wrapper.find_all('a', href=True):
                        href = a_tag.get('href', '')
                        text = a_tag.text.strip().lower()
                        
                        if 'filecrypt.cc' in href:
                            debug(f"Filecrypt-Link in bbWrapper gefunden: {href}")
                            debug(f"  Link-Text: '{text}'")
                            
                            # Sammle alle Links
                            download_links.append((href, text))
                            
                            # Wenn "rapidgator" im Text oder in der Nähe vorkommt
                            if 'rapidgator' in text:
                                debug(f"Direkter Rapidgator-Link in bbWrapper gefunden: {href}")
                                rapidgator_links.append(href)
        
        # 5. FALLBACK: VERSUCHE ALLE FILECRYPT-LINKS
        if not rapidgator_links and not download_links:
            debug("==== FALLBACK: ALLE FILECRYPT-LINKS ====")
            
            for a_tag in all_links:
                href = a_tag.get('href', '')
                text = a_tag.text.strip()
                
                if 'filecrypt.cc' in href:
                    download_links.append((href, text))
                    debug(f"Filecrypt-Link (Fallback): {href} - '{text}'")
            
            # Wenn keine expliziten Rapidgator-Links gefunden wurden, versuche heuristisch zu entscheiden
            if download_links:
                for href, text in download_links:
                    # Bevorzuge Links mit "rapidgator" im Text
                    if 'rapidgator' in text.lower():
                        debug(f"Bevorzugter Rapidgator-Link (aus Fallback): {href}")
                        rapidgator_links.append(href)
                        break
                
                # Wenn immer noch nichts gefunden, nimm den ersten Link
                if not rapidgator_links:
                    first_link = download_links[0][0]
                    debug(f"Kein expliziter Rapidgator-Link gefunden, verwende ersten Filecrypt-Link: {first_link}")
                    rapidgator_links.append(first_link)
        
        # 6. EXTREMER FALLBACK: TEXT-EXTRAKTION
        if not rapidgator_links:
            debug("==== EXTREMER FALLBACK: TEXT-EXTRAKTION ====")
            
            # Suche nach filecrypt.cc Links im Volltext
            text_content = soup.get_text()
            urls = re.findall(r'https?://filecrypt\.cc/[^\s<>"]+', text_content)
            
            if urls:
                debug(f"URLs im Text gefunden: {urls}")
                for url in urls:
                    debug(f"URL aus Text: {url}")
                rapidgator_links = urls
        
        # Ergebnis
        if not rapidgator_links:
            info(f"Keine Filecrypt/Rapidgator-Links auf der Seite {url} gefunden")
            debug(f"Bitte melde dich manuell an und prüfe die Links: {url}")
            debug(f"========== GET_DL_DOWNLOAD_LINK ENDE (keine Links gefunden) =========")
            return None
        
        result_link = rapidgator_links[0]
        debug(f"Gefundener Link: {result_link}")
        debug(f"========== GET_DL_DOWNLOAD_LINK ENDE (erfolgreich) =========")
        
        return result_link
    
    except Exception as e:
        import traceback
        debug(f"========== FEHLER IN GET_DL_DOWNLOAD_LINK ==========")
        debug(f"Fehler beim Extrahieren des Download-Links: {str(e)}")
        debug(f"Stacktrace:")
        debug(traceback.format_exc())
        debug(f"========== GET_DL_DOWNLOAD_LINK ENDE (mit Fehler) =========")
        info(f"Fehler beim Extrahieren des Download-Links: {e}")
        return None 


def get_all_download_links(shared_state, url):
    """
    Extrahiert alle Download-Links von einer data-load.me Thread-URL
    Unterstützt: FileCrypt, RapidGator, DDownload, KeepLinks, und andere Hoster
    """
    dl = shared_state.values["config"]("Hostnames").get("dl")
    if not dl:
        debug("Hostname für DL nicht konfiguriert")
        return []
    
    # Prüfe, ob die URL zu data-load.me gehört
    if not url or dl not in url:
        debug(f"URL {url} ist keine gültige DL-URL")
        return []
    
    debug(f"[DL-LINKS] Extrahiere alle Download-Links von: {url}")
    
    # Session abrufen
    session = get_persistent_session(shared_state)
    if not session:
        debug("Konnte keine gültige DL-Session abrufen")
        return []
    
    try:
        # Topic-Seite laden mit zusätzlichen Headern
        session.headers.update({
            "Referer": f"https://{dl}/",
            "Cache-Control": "no-cache"
        })
        
        response = session.get(url, timeout=15)
        
        if response.status_code != 200:
            debug(f"Thread nicht erreichbar (Status: {response.status_code})")
            return []
        
        # Prüfe auf Login-Aufforderung
        if "bitte anmelden oder registrieren um links zu sehen" in response.text.lower():
            debug("[DL-LINKS] Session ist nicht eingeloggt - versuche Session-Erneuerung")
            
            # Lösche die alte Session, damit eine neue erstellt wird
            if hasattr(shared_state, 'update'):
                shared_state.update("dl_session", None)
            
            # Neue Session holen (einmaliger Versuch)
            session = get_persistent_session(shared_state)
            if not session:
                debug("[DL-LINKS] Session-Erneuerung fehlgeschlagen")
                return []
            
            # Versuche erneut mit neuer Session
            response = session.get(url, timeout=15)
            if response.status_code != 200:
                debug(f"Thread nach Session-Erneuerung nicht erreichbar (Status: {response.status_code})")
                return []
            
            # Erneute Prüfung - wenn immer noch Login erforderlich, dann aufgeben
            if "bitte anmelden oder registrieren um links zu sehen" in response.text.lower():
                debug("[DL-LINKS] Links trotz Session-Erneuerung nicht sichtbar - möglicherweise Credentials falsch")
                return []
        
        debug(f"[DL-LINKS] Seite erfolgreich geladen, Parse HTML...")
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Debug-Informationen über die Seite
        page_title = soup.title.string if soup.title else "Unbekannt"
        debug(f"[DL-LINKS] Seitentitel: {page_title}")
        
        # Alle Download-Links sammeln
        download_links = []
        
        # Bekannte Download-Domains (Priorität: direkte Hoster > Container)
        direct_hosters = [
            'rapidgator.net', 'uploaded.net', 'turbobit.net', 
            'nitroflare.com', '1fichier.com', 'ddownload.com',
            'katfile.com', 'mexashare.com', 'depositfiles.com'
        ]
        
        container_services = [
            'filecrypt.cc', 'filecrypt.co', 'keeplinks.org', 
            'protect-links.com', 'safelinking.net', 'linkprotect.org'
        ]
        
        all_services = direct_hosters + container_services
        
        # Sammle Statistiken über alle Links
        all_links = soup.find_all('a', href=True)
        link_stats = {}
        for service in all_services:
            link_stats[service] = 0
        
        debug(f"[DL-LINKS] Analysiere {len(all_links)} Links auf der Seite...")
        
        # Methode 1: Direkte Link-Suche mit detailliertem Debugging
        for i, link in enumerate(all_links):
            href = link.get('href', '').strip()
            link_text = link.text.strip()
            
            for service in all_services:
                if service in href.lower():
                    link_stats[service] += 1
                if href not in download_links:
                    download_links.append(href)
                        debug(f"[DL-LINKS] Download-Link gefunden ({service}): {href}")
                        if link_text:
                            debug(f"[DL-LINKS]   Link-Text: '{link_text}'")
                    break
        
        # Debug-Ausgabe der Link-Statistiken
        found_services = {k: v for k, v in link_stats.items() if v > 0}
        if found_services:
            debug(f"[DL-LINKS] Link-Statistiken: {found_services}")
        else:
            debug("[DL-LINKS] Keine bekannten Download-Services in direkten Links gefunden")
        
        # Methode 2: Suche in Post-Content (XenForo-spezifisch)
        if not download_links:
            debug("[DL-LINKS] Suche in Post-Content...")
            post_contents = soup.find_all('div', class_='bbWrapper')
            debug(f"[DL-LINKS] Gefunden {len(post_contents)} Post-Content-Bereiche")
            
            for post in post_contents:
                post_links = post.find_all('a', href=True)
                for link in post_links:
                    href = link.get('href', '').strip()
                    for service in all_services:
                        if service in href.lower():
                            if href not in download_links:
                                download_links.append(href)
                                debug(f"[DL-LINKS] Download-Link in Post gefunden ({service}): {href}")
        
        # Methode 3: Text-Pattern-Suche (Fallback)
        if not download_links:
            debug("[DL-LINKS] Fallback: Text-Pattern-Suche...")
            text_content = soup.get_text()
            
            # Pattern für verschiedene Services
            patterns = []
            for domain in all_services:
                patterns.extend([
                    rf'https?://{re.escape(domain)}/[^\s<>"\']+',
                    rf'{re.escape(domain)}/[^\s<>"\']+',
                ])
            
            for pattern in patterns:
                matches = re.findall(pattern, text_content, re.IGNORECASE)
                for match in matches:
                    if not match.startswith('http'):
                        match = f"https://{match}"
                    if match not in download_links:
                        download_links.append(match)
                        debug(f"[DL-LINKS] Download-Link (Pattern) gefunden: {match}")
        
        # Priorisierung: Direkte Hoster zuerst, dann Container
        prioritized_links = []
        
        # Zuerst direkte Hoster
        for link in download_links:
            if any(domain in link.lower() for domain in direct_hosters):
                prioritized_links.append(link)
        
        # Dann Container-Services
        for link in download_links:
            if any(domain in link.lower() for domain in container_services):
                if link not in prioritized_links:
                    prioritized_links.append(link)
        
        debug(f"[DL-LINKS] Insgesamt {len(prioritized_links)} Download-Links gefunden (priorisiert)")
        
        # Maximal 5 Links zurückgeben
        return prioritized_links[:5]
        
    except Exception as e:
        debug(f"[DL-LINKS] Fehler beim Extrahieren der Download-Links: {e}")
        return []


def get_filecrypt_links(url):
    """
    Extrahiert alle FileCrypt-Links von einer data-load.me URL
    Basiert auf der bewährten Demo-Implementierung
    """
    from quasarr.storage.setup import get_shared_state
    shared_state = get_shared_state()
    
    dl = shared_state.values["config"]("Hostnames").get("dl")
    if not dl:
        debug("Hostname für DL nicht konfiguriert")
        return []
    
    # Prüfe, ob die URL zu data-load.me gehört
    if not url or dl not in url:
        debug(f"URL {url} ist keine gültige DL-URL")
        return []
    
    debug(f"Extrahiere FileCrypt-Links von: {url}")
    
    # Session abrufen
    session = get_persistent_session(shared_state)
    if not session:
        debug("Konnte keine gültige DL-Session abrufen")
        return []
    
    try:
        # Topic-Seite laden
        response = session.get(url, timeout=15)
        
        if response.status_code != 200:
            debug(f"Topic nicht erreichbar (Status: {response.status_code})")
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Suche nach FileCrypt Links (bewährte Demo-Methode)
        filecrypt_links = []
        
        # Methode 1: Direkte Link-Suche
        all_links = soup.find_all('a', href=True)
        for link in all_links:
            href = link.get('href', '')
            if any(domain in href.lower() for domain in ['filecrypt.cc', 'filecrypt.co']):
                if href not in filecrypt_links:
                    filecrypt_links.append(href)
                    debug(f"FileCrypt-Link gefunden: {href}")
        
        # Methode 2: Text-Pattern-Suche (Fallback)
        if not filecrypt_links:
            text_content = soup.get_text()
            patterns = [
                r'https?://filecrypt\.(?:cc|co)/[^\s<>"\']+',
                r'filecrypt\.(?:cc|co)/[^\s<>"\']+',
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, text_content, re.IGNORECASE)
                for match in matches:
                    if not match.startswith('http'):
                        match = f"https://{match}"
                    if match not in filecrypt_links:
                        filecrypt_links.append(match)
        
        debug(f"Insgesamt {len(filecrypt_links)} FileCrypt-Links gefunden")
        return filecrypt_links[:10]  # Maximal 10 Links
        
    except Exception as e:
        debug(f"Fehler beim Extrahieren der FileCrypt-Links: {e}")
        return []