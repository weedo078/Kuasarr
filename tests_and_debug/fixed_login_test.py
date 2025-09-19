#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Korrigierter Login-Test für data-load.me

import requests
from bs4 import BeautifulSoup
import re
import time
import random

# Login-Daten
DL_USERNAME = "weedo078"
DL_PASSWORD = "monEY125\""
DL_HOST = "www.data-load.me"

def debug(msg):
    print(f"[DEBUG] {msg}")

def setup_session():
    """Session mit realistischen Headers einrichten"""
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'de-DE,de;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
    })
    return session

def extract_csrf_token(soup):
    """CSRF-Token mit verschiedenen Methoden extrahieren"""
    
    # Methode 1: _xfToken input field
    csrf_input = soup.find('input', {'name': '_xfToken'})
    if csrf_input and csrf_input.get('value'):
        debug(f"CSRF-Token aus input gefunden: {csrf_input.get('value')[:20]}...")
        return csrf_input.get('value')
    
    # Methode 2: meta tag
    csrf_meta = soup.find('meta', {'name': 'csrf-token'})
    if csrf_meta and csrf_meta.get('content'):
        debug(f"CSRF-Token aus meta gefunden: {csrf_meta.get('content')[:20]}...")
        return csrf_meta.get('content')
    
    # Methode 3: data-csrf attribute im html tag
    html_tag = soup.find('html')
    if html_tag and html_tag.get('data-csrf'):
        debug(f"CSRF-Token aus html data-csrf gefunden: {html_tag.get('data-csrf')[:20]}...")
        return html_tag.get('data-csrf')
    
    # Methode 4: JavaScript variable suchen
    script_tags = soup.find_all('script')
    for script in script_tags:
        if script.string:
            # Suche nach verschiedenen JS-Variablen-Mustern
            patterns = [
                r'_xfToken["\']?\s*:\s*["\']([^"\']+)["\']',
                r'csrf["\']?\s*:\s*["\']([^"\']+)["\']',
                r'XF\.config\.csrf\s*=\s*["\']([^"\']+)["\']',
                r'csrfToken["\']?\s*:\s*["\']([^"\']+)["\']'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, script.string, re.IGNORECASE)
                if match:
                    token = match.group(1)
                    debug(f"CSRF-Token aus JavaScript gefunden: {token[:20]}...")
                    return token
    
    debug("Kein CSRF-Token gefunden")
    return None

def improved_login(session):
    """Verbesserter Login mit besserer Token-Extraktion"""
    
    try:
        print("[*] Starte verbesserter Login-Prozess...")
        
        # Schritt 1: Startseite laden um Session zu etablieren
        print("[*] Lade Startseite...")
        home_response = session.get(f"https://{DL_HOST}/", timeout=10)
        home_response.raise_for_status()
        debug(f"Startseite geladen: {home_response.status_code}")
        
        # Kurze Pause
        time.sleep(1)
        
        # Schritt 2: Login-Seite laden
        print("[*] Lade Login-Seite...")
        login_url = f"https://{DL_HOST}/login/"
        
        # Headers für Login-Seiten-Request
        session.headers.update({
            'Referer': f'https://{DL_HOST}/',
        })
        
        login_response = session.get(login_url, timeout=10)
        login_response.raise_for_status()
        debug(f"Login-Seite geladen: {login_response.status_code}")
        
        # HTML parsen
        soup = BeautifulSoup(login_response.text, 'html.parser')
        
        # Debug: Schaue nach Login-Form
        login_form = soup.find('form')
        if login_form:
            debug(f"Login-Form gefunden: {login_form.get('action', 'keine action')}")
            
            # Alle Input-Felder auflisten
            inputs = login_form.find_all('input')
            debug(f"Gefundene Input-Felder: {len(inputs)}")
            for inp in inputs:
                debug(f"  - {inp.get('name', 'unnamed')}: {inp.get('type', 'text')} = {str(inp.get('value', ''))[:20]}")
        
        # Schritt 3: CSRF-Token extrahieren
        csrf_token = extract_csrf_token(soup)
        
        if not csrf_token:
            print("[!] Kein CSRF-Token gefunden, versuche trotzdem...")
        
        # Schritt 4: Login-Daten vorbereiten
        login_data = {
            'login': DL_USERNAME,
            'password': DL_PASSWORD,
            'remember': '1',
            '_xfRedirect': f'https://{DL_HOST}/',
        }
        
        # CSRF-Token hinzufügen falls vorhanden
        if csrf_token:
            login_data['_xfToken'] = csrf_token
        
        # Schritt 5: Login durchführen
        print("[*] Sende Login-Daten...")
        
        # Headers für POST-Request
        session.headers.update({
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': f'https://{DL_HOST}',
            'Referer': login_url,
        })
        
        debug(f"Login-Daten: {dict((k, v if k != 'password' else '*' * len(v)) for k, v in login_data.items())}")
        
        # Login-POST senden
        login_post_response = session.post(login_url, data=login_data, timeout=10, allow_redirects=True)
        login_post_response.raise_for_status()
        
        debug(f"Login-Response: {login_post_response.status_code}, URL: {login_post_response.url}")
        
        # Schritt 6: Login-Erfolg prüfen
        # Verschiedene Erfolgsindikatoren prüfen
        response_text = login_post_response.text.lower()
        response_url = login_post_response.url.lower()
        
        # Erfolgs-Indikatoren
        success_indicators = [
            DL_USERNAME.lower() in response_text,
            'logout' in response_text,
            'abmelden' in response_text,
            'account' in response_text,
            'login' not in response_url or response_url == f'https://{DL_HOST}/'
        ]
        
        # Fehlschlag-Indikatoren
        failure_indicators = [
            'error' in response_text,
            'fehler' in response_text,
            'ungültig' in response_text,
            'falsch' in response_text,
            'invalid' in response_text,
            'incorrect' in response_text,
        ]
        
        success_count = sum(success_indicators)
        failure_count = sum(failure_indicators)
        
        debug(f"Erfolgs-Indikatoren: {success_count}/5")
        debug(f"Fehlschlag-Indikatoren: {failure_count}")
        
        if success_count >= 2 and failure_count == 0:
            print("[+] Login erfolgreich!")
            return True
        else:
            print(f"[-] Login wahrscheinlich fehlgeschlagen")
            debug(f"Response (erste 300 Zeichen): {login_post_response.text[:300]}")
            
            # Trotzdem als erfolgreich behandeln wenn wir umgeleitet wurden
            if 'login' not in response_url:
                print("[?] Keine Fehler gefunden, behandle als erfolgreich...")
                return True
            
            return False
            
    except Exception as e:
        print(f"[-] Fehler beim Login: {e}")
        return False

def test_login_and_thread():
    """Teste Login und dann Thread-Zugriff"""
    
    print("=== VERBESSERTER LOGIN & THREAD TEST ===")
    
    session = setup_session()
    
    # Login durchführen
    if not improved_login(session):
        print("[-] Login fehlgeschlagen, breche ab")
        return
    
    # Reset headers nach Login
    session.headers.update({
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Content-Type': '',  # Reset content type
    })
    
    # Kurze Pause nach Login
    time.sleep(2)
    
    # Thread-Seite testen
    thread_url = "https://www.data-load.me/threads/the-last-of-us-s02-german-aac-1080p-web-x265-w00t.921932/"
    
    try:
        print(f"[*] Teste Thread-Zugriff nach Login...")
        print(f"[+] Lade Thread: {thread_url}")
        
        response = session.get(thread_url, timeout=10)
        response.raise_for_status()
        
        print(f"[+] Thread geladen (Status: {response.status_code})")
        
        # Speichere für Analyse
        with open('thread_after_login.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
        print("[+] HTML gespeichert als 'thread_after_login.html'")
        
        # Suche nach FileCrypt-Links
        text_content = response.text
        
        # FileCrypt-Pattern
        filecrypt_patterns = [
            r'https?://(?:www\.)?filecrypt\.cc/[^\s\<\>\"\']+',
            r'https?://(?:www\.)?filecrypt\.co/[^\s\<\>\"\']+',
            r'filecrypt\.cc/[A-Za-z0-9/\.]+',
            r'filecrypt\.co/[A-Za-z0-9/\.]+',
            r'Container/[A-F0-9]+\.html',
        ]
        
        filecrypt_links = []
        
        for pattern in filecrypt_patterns:
            matches = re.findall(pattern, text_content, re.IGNORECASE)
            for match in matches:
                if 'Container/' in match and not match.startswith('http'):
                    match = f'https://filecrypt.cc/{match}'
                elif not match.startswith('http') and 'filecrypt' in match:
                    match = f'https://{match}'
                
                if match not in filecrypt_links:
                    filecrypt_links.append(match)
                    print(f"[+] FileCrypt-Link gefunden: {match}")
        
        # Ergebnis
        print(f"\n[+] ERGEBNIS: {len(filecrypt_links)} FileCrypt-Links nach Login gefunden!")
        
        if filecrypt_links:
            print("\n[*] Gefundene FileCrypt-Links:")
            for i, link in enumerate(filecrypt_links, 1):
                print(f"  {i}. {link}")
        else:
            print("\n[!] Keine FileCrypt-Links gefunden - möglicherweise Login-Problem oder andere Ursache")
            
            # Debug: Schaue nach anderen Download-Links
            other_patterns = [
                r'https?://[^\s]+\.(?:rar|zip|7z)',
                r'https?://(?:rapidgator|uploaded|turbobit|nitroflare)\.(?:net|com)/[^\s]+',
            ]
            
            other_links = []
            for pattern in other_patterns:
                matches = re.findall(pattern, text_content, re.IGNORECASE)
                other_links.extend(matches)
            
            if other_links:
                print(f"[!] Aber {len(other_links)} andere Download-Links gefunden:")
                for link in other_links[:3]:
                    print(f"  - {link}")
        
        return filecrypt_links
        
    except Exception as e:
        print(f"[-] Fehler beim Thread-Zugriff: {e}")
        return []

if __name__ == "__main__":
    test_login_and_thread() 