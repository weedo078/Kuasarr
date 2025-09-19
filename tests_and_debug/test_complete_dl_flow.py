#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Vollständiger Test für data-load.me Integration mit Login und FileCrypt-Extraktion

import requests
from bs4 import BeautifulSoup
import re
import time
import random
import html
from urllib.parse import urljoin, urlparse, parse_qs

# Login-Daten
DL_USERNAME = "weedo078"
DL_PASSWORD = "monEY125\""
DL_HOST = "www.data-load.me"

# User-Agent für legitimere Anfragen
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36"

def debug(msg):
    print(f"[DEBUG] {msg}")

def info(msg):
    print(f"[INFO] {msg}")

def setup_session():
    """Eine Session mit Browser-ähnlichen Headers einrichten"""
    session = requests.Session()
    session.headers.update({
        'User-Agent': USER_AGENT,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'de-DE,de;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Cache-Control': 'max-age=0',
    })
    return session

def login_to_dataload(session):
    """Login zu data-load.me"""
    try:
        print("[*] Starte Login-Prozess...")
        
        # Schritt 1: Login-Seite laden
        login_url = f"https://{DL_HOST}/login/"
        response = session.get(login_url, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Schritt 2: CSRF-Token extrahieren
        csrf_token = None
        csrf_input = soup.find('input', {'name': '_xfToken'})
        if csrf_input:
            csrf_token = csrf_input.get('value')
            debug(f"CSRF-Token gefunden: {csrf_token[:20]}...")
        else:
            debug("Kein CSRF-Token gefunden")
        
        # Schritt 3: Login-Daten senden
        login_data = {
            'login': DL_USERNAME,
            'password': DL_PASSWORD,
            'remember': '1',
            '_xfRedirect': f'https://{DL_HOST}/',
            '_xfToken': csrf_token
        }
        
        # Headers für POST-Request
        session.headers.update({
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': f'https://{DL_HOST}',
            'Referer': login_url,
        })
        
        # Login-Request senden
        response = session.post(login_url, data=login_data, timeout=10, allow_redirects=True)
        response.raise_for_status()
        
        # Schritt 4: Login-Erfolg prüfen
        if 'login' not in response.url.lower() and response.status_code == 200:
            print("[+] Login erfolgreich!")
            
            # Prüfe auf Benutzer-Indikator im HTML
            if DL_USERNAME.lower() in response.text.lower():
                print(f"[+] Benutzer '{DL_USERNAME}' erkannt im Response")
            
            return True
        else:
            print(f"[-] Login fehlgeschlagen. Status: {response.status_code}, URL: {response.url}")
            debug(f"Response-Inhalt (erste 500 Zeichen): {response.text[:500]}")
            return False
            
    except Exception as e:
        print(f"[-] Fehler beim Login: {e}")
        return False

def test_search_with_login():
    """Teste die Suchfunktion mit Login"""
    
    print("[*] === TEST DER SUCHFUNKTION MIT LOGIN ===")
    
    session = setup_session()
    
    # Login durchführen
    if not login_to_dataload(session):
        print("[-] Login fehlgeschlagen, breche ab")
        return None
    
    # Reset headers nach Login
    session.headers.update({
        'Content-Type': 'text/html',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    })
    
    # Teste die spezifische Such-URL
    search_url = "https://www.data-load.me/search/35701133/?q=the+last+of+us+s02&c[title_only]=1&o=relevance"
    
    try:
        print(f"[+] Teste Such-URL: {search_url}")
        
        time.sleep(random.uniform(1, 2))  # Etwas längere Pause nach Login
        
        response = session.get(search_url, timeout=10)
        response.raise_for_status()
        
        print(f"[+] Suchergebnisse geladen (Status: {response.status_code})")
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Parser-Logik anwenden
        results = []
        
        # METHODE 1: Moderne data-load.me Struktur (block-row + contentRow)
        block_rows = soup.find_all('li', class_='block-row')
        debug(f"Gefundene block-row Elemente: {len(block_rows)}")
        
        for row in block_rows:
            content_row = row.find('div', class_='contentRow')
            if content_row:
                results.append(content_row)
        
        # METHODE 2: Fallback für structItem-Struktur
        if not results:
            struct_items = soup.find_all('div', class_='structItem')
            debug(f"Fallback: Gefundene structItem Elemente: {len(struct_items)}")
            results.extend(struct_items)
        
        debug(f"Insgesamt extrahierte Such-Ergebnisse: {len(results)}")
        
        if not results:
            print("[-] Keine Ergebnisse gefunden!")
            return session
        
        print(f"[+] {len(results)} Ergebnisse gefunden")
        print()
        
        # Verarbeite die ersten 5 Ergebnisse und suche nach dem w00t Release
        target_found = False
        for i, result in enumerate(results[:10]):
            # Titel und Link extrahieren
            title_elem = None
            link = None
            
            # contentRow-Struktur
            content_title = result.find('h3', class_='contentRow-title')
            if content_title:
                title_elem = content_title.find('a')
                if title_elem:
                    link = title_elem.get('href', '')
            
            if title_elem and title_elem.text.strip():
                title = title_elem.get_text(strip=True)
                title = html.unescape(title)
                
                print(f"[*] === ERGEBNIS {i+1} ===")
                print(f"[+] Titel: {title}")
                print(f"[+] Link: {link}")
                
                # Prüfe ob es das w00t Release ist
                if 'w00t' in title and 'GERMAN AAC 1080p WEB x265' in title:
                    print(f"[★] ZIEL-RELEASE GEFUNDEN: {title}")
                    target_found = True
                    
                    # Teste diesen Thread
                    if link:
                        thread_url = urljoin(f"https://{DL_HOST}", link)
                        print(f"[+] Thread-URL: {thread_url}")
                        test_thread_page(session, thread_url)
                
                print()
        
        if not target_found:
            print("[!] Das w00t-Release wurde nicht in den ersten 10 Ergebnissen gefunden")
        
        return session
        
    except Exception as e:
        print(f"[-] Fehler bei der Suche: {e}")
        return session

def test_thread_page(session, thread_url):
    """Teste eine Thread-Seite und extrahiere FileCrypt-Links"""
    
    print("[*] === THREAD-SEITEN-ANALYSE ===")
    
    try:
        print(f"[+] Lade Thread: {thread_url}")
        
        time.sleep(random.uniform(1, 2))
        
        response = session.get(thread_url, timeout=10)
        response.raise_for_status()
        
        print(f"[+] Thread geladen (Status: {response.status_code})")
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Suche nach FileCrypt-Links
        filecrypt_links = []
        
        # Alle Links im Thread durchsuchen
        all_links = soup.find_all('a', href=True)
        
        for link in all_links:
            href = link.get('href', '')
            
            # Prüfe auf FileCrypt-Links
            if 'filecrypt.cc' in href or 'filecrypt.co' in href:
                filecrypt_links.append(href)
                print(f"[+] FileCrypt-Link gefunden: {href}")
        
        # Auch nach versteckten/kodierten Links suchen
        text_content = soup.get_text()
        
        # Regex für FileCrypt-Links im Text
        filecrypt_pattern = r'https?://(?:www\.)?filecrypt\.c[co]/[^\s]+'
        text_links = re.findall(filecrypt_pattern, text_content, re.IGNORECASE)
        
        for link in text_links:
            if link not in filecrypt_links:
                filecrypt_links.append(link)
                print(f"[+] FileCrypt-Link im Text gefunden: {link}")
        
        # Suche nach anderen Download-Hostern
        other_hosts = []
        host_patterns = [
            r'https?://(?:www\.)?rapidgator\.net/[^\s]+',
            r'https?://(?:www\.)?turbobit\.net/[^\s]+',
            r'https?://(?:www\.)?nitroflare\.com/[^\s]+',
            r'https?://(?:www\.)?uploaded\.net/[^\s]+',
            r'https?://(?:www\.)?mixdrop\.co/[^\s]+',
        ]
        
        for pattern in host_patterns:
            matches = re.findall(pattern, text_content, re.IGNORECASE)
            other_hosts.extend(matches)
        
        print(f"[+] Insgesamt {len(filecrypt_links)} FileCrypt-Links gefunden")
        print(f"[+] Insgesamt {len(other_hosts)} andere Host-Links gefunden")
        
        if filecrypt_links:
            print("\n[*] FileCrypt-Links:")
            for i, link in enumerate(filecrypt_links[:5], 1):
                print(f"  {i}. {link}")
        
        if other_hosts:
            print("\n[*] Andere Download-Links:")
            for i, link in enumerate(other_hosts[:5], 1):
                print(f"  {i}. {link}")
        
        return filecrypt_links
        
    except Exception as e:
        print(f"[-] Fehler beim Laden der Thread-Seite: {e}")
        return []

def test_direct_thread():
    """Teste direkt die bekannte Thread-URL"""
    
    print("[*] === DIREKTER THREAD-TEST ===")
    
    session = setup_session()
    
    # Login durchführen
    if not login_to_dataload(session):
        print("[-] Login fehlgeschlagen, teste ohne Login")
    
    # Teste die bekannte Thread-URL
    thread_url = "https://www.data-load.me/threads/the-last-of-us-s02-german-aac-1080p-web-x265-w00t.921932/"
    
    filecrypt_links = test_thread_page(session, thread_url)
    
    return filecrypt_links

if __name__ == "__main__":
    print("=== VOLLSTÄNDIGER DATA-LOAD.ME TEST ===")
    print(f"Username: {DL_USERNAME}")
    print(f"Password: {'*' * len(DL_PASSWORD)}")
    print()
    
    # Test 1: Suche mit Login
    session = test_search_with_login()
    
    print("\n" + "="*50)
    
    # Test 2: Direkter Thread-Test
    test_direct_thread() 