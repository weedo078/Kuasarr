#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Test der data-load.me Integration mit Cookie-Authentifizierung

import json
import requests
from bs4 import BeautifulSoup
import re

def test_dl_cookie_integration():
    """Testet die data-load.me Integration mit Cookie-Authentifizierung"""
    
    print("=== DATA-LOAD.ME COOKIE INTEGRATION TEST ===")
    
    # Session mit Cookies erstellen
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7',
        'Connection': 'keep-alive',
    })
    
    # Cookies laden
    try:
        with open('dl_cookies.json', 'r') as f:
            cookie_data = json.load(f)
        
        for name, value in cookie_data['cookies'].items():
            session.cookies.set(name, value, domain='www.data-load.me')
        
        print(f"✅ {len(cookie_data['cookies'])} Cookies geladen")
        
    except Exception as e:
        print(f"❌ Fehler beim Cookie-Laden: {e}")
        return False
    
    # TEST 1: Login-Status prüfen
    print("\n1. Prüfe Login-Status...")
    try:
        response = session.get('https://www.data-load.me/account/', timeout=10)
        content = response.text.lower()
        
        if 'logout' in content or 'abmelden' in content:
            print("   ✅ Erfolgreich eingeloggt!")
        else:
            print("   ⚠️ Login-Status unklar")
            
    except Exception as e:
        print(f"   ❌ Login-Test fehlgeschlagen: {e}")
    
    # TEST 2: Thread-Zugriff mit FileCrypt-Links
    print("\n2. Teste Thread-Zugriff...")
    thread_url = "https://www.data-load.me/threads/the-last-of-us-s02-german-aac-1080p-web-x265-w00t.921932/"
    
    try:
        response = session.get(thread_url, timeout=15)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            # Suche FileCrypt-Links
            filecrypt_patterns = [
                r'https://filecrypt\.cc/[^\s<>"\']+',
                r'https://filecrypt\.co/[^\s<>"\']+',
                r'filecrypt\.cc/Container/[A-F0-9]+\.html',
            ]
            
            filecrypt_links = []
            for pattern in filecrypt_patterns:
                matches = re.findall(pattern, response.text, re.IGNORECASE)
                for match in matches:
                    if not match.startswith('http'):
                        match = f'https://{match}'
                    if match not in filecrypt_links:
                        filecrypt_links.append(match)
            
            print(f"   FileCrypt-Links gefunden: {len(filecrypt_links)}")
            for i, link in enumerate(filecrypt_links[:3], 1):
                print(f"      {i}. {link}")
            
            if filecrypt_links:
                print("   ✅ FileCrypt-Extraktion funktioniert!")
                return True
            else:
                print("   ⚠️ Keine FileCrypt-Links gefunden")
                
        else:
            print(f"   ❌ Unerwarteter Status-Code: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Thread-Test fehlgeschlagen: {e}")
    
    # TEST 3: Suche testen
    print("\n3. Teste Suchfunktion...")
    try:
        search_url = "https://www.data-load.me/search/?q=test"
        response = session.get(search_url, timeout=10)
        print(f"   Such-Status: {response.status_code}")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Suche nach Thread-Links
            thread_links = []
            for link in soup.find_all('a', href=True):
                href = link.get('href')
                if '/threads/' in href:
                    if not href.startswith('http'):
                        href = f"https://www.data-load.me{href}"
                    thread_links.append(href)
            
            print(f"   Thread-Links gefunden: {len(thread_links)}")
            if thread_links:
                print("   ✅ Suchfunktion funktioniert!")
            else:
                print("   ⚠️ Keine Thread-Links in Suchergebnissen")
                
    except Exception as e:
        print(f"   ❌ Such-Test fehlgeschlagen: {e}")
    
    print("\n=== TEST ABGESCHLOSSEN ===")
    return False

if __name__ == "__main__":
    success = test_dl_cookie_integration()
    
    if success:
        print("\n🎉 VOLLSTÄNDIGER ERFOLG!")
        print("Die data-load.me Integration funktioniert mit Cookie-Authentifizierung!")
    else:
        print("\n⚠️ Tests teilweise erfolgreich - Details siehe oben") 