#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# PROOF OF CONCEPT - Login und FileCrypt-Extraktion Test

import requests
from bs4 import BeautifulSoup
import re
import time

# Test-Credentials
USERNAME = "weedo078"
PASSWORD = "monEY125\""
HOST = "www.data-load.me"

def simple_login_test():
    """Einfacher, direkter Login-Test ohne komplexe Logik"""
    
    print("=" * 60)
    print("PROOF OF CONCEPT: LOGIN UND FILECRYPT-EXTRAKTION")
    print("=" * 60)
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36'
    })
    
    try:
        # SCHRITT 1: Startseite besuchen
        print("\n[1] Besuche Startseite...")
        home_response = session.get(f"https://{HOST}/", timeout=15)
        print(f"    Status: {home_response.status_code}")
        
        # SCHRITT 2: Login-Seite laden
        print("\n[2] Lade Login-Seite...")
        login_response = session.get(f"https://{HOST}/login/", timeout=15)
        print(f"    Status: {login_response.status_code}")
        
        # SCHRITT 3: Token suchen (mehrere Methoden)
        soup = BeautifulSoup(login_response.text, 'html.parser')
        
        # Methode A: _xfToken input
        token = None
        token_input = soup.find('input', {'name': '_xfToken'})
        if token_input:
            token = token_input.get('value')
            print(f"    Token gefunden (input): {token[:20]}...")
        
        # Methode B: HTML data-csrf
        if not token:
            html_tag = soup.find('html')
            if html_tag:
                token = html_tag.get('data-csrf')
                if token:
                    print(f"    Token gefunden (html): {token[:20]}...")
        
        # Methode C: JavaScript-Suche
        if not token:
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string:
                    match = re.search(r'"csrf":\s*"([^"]+)"', script.string)
                    if match:
                        token = match.group(1)
                        print(f"    Token gefunden (JS): {token[:20]}...")
                        break
        
        if not token:
            print("    [!] Kein Token gefunden - versuche ohne")
        
        # SCHRITT 4: Login-Daten zusammenstellen
        login_data = {
            'login': USERNAME,
            'password': PASSWORD,
            'remember': '1'
        }
        
        if token:
            login_data['_xfToken'] = token
        
        print(f"\n[3] Sende Login-Request...")
        print(f"    Username: {USERNAME}")
        print(f"    Password: ***")
        print(f"    Token: {'Ja' if token else 'Nein'}")
        
        # SCHRITT 5: Login durchführen
        session.headers.update({
            'Referer': f'https://{HOST}/login/',
            'Content-Type': 'application/x-www-form-urlencoded'
        })
        
        login_post = session.post(f"https://{HOST}/login/", data=login_data, timeout=15, allow_redirects=True)
        print(f"    Login-Status: {login_post.status_code}")
        print(f"    Redirect-URL: {login_post.url}")
        
        # SCHRITT 6: Login-Erfolg prüfen
        print(f"\n[4] Prüfe Login-Erfolg...")
        
        # Prüfe verschiedene Indikatoren
        response_text = login_post.text.lower()
        
        success_checks = {
            'Username im Text': USERNAME.lower() in response_text,
            'Logout-Link vorhanden': 'logout' in response_text or 'abmelden' in response_text,
            'Kein Login in URL': 'login' not in login_post.url.lower(),
            'Account-Bereich': 'account' in response_text or 'konto' in response_text
        }
        
        print("    Login-Indikatoren:")
        success_count = 0
        for check, result in success_checks.items():
            status = "✓" if result else "✗"
            print(f"      {status} {check}: {result}")
            if result:
                success_count += 1
        
        login_successful = success_count >= 2
        print(f"\n    >>> LOGIN {'ERFOLGREICH' if login_successful else 'FEHLGESCHLAGEN'} ({success_count}/4 Checks) <<<")
        
        if not login_successful:
            print("\n[!] Login fehlgeschlagen - kann FileCrypt-Test nicht durchführen")
            return False
        
        # SCHRITT 7: Thread-Seite mit Login testen
        print(f"\n[5] Teste Thread-Seite nach Login...")
        
        thread_url = "https://www.data-load.me/threads/the-last-of-us-s02-german-aac-1080p-web-x265-w00t.921932/"
        print(f"    URL: {thread_url}")
        
        # Reset Content-Type für normale Requests
        session.headers['Content-Type'] = 'text/html'
        
        thread_response = session.get(thread_url, timeout=15)
        print(f"    Status: {thread_response.status_code}")
        
        # SCHRITT 8: FileCrypt-Links suchen
        print(f"\n[6] Suche nach FileCrypt-Links...")
        
        text_content = thread_response.text
        
        # Verschiedene Suchmuster
        patterns = [
            r'https://filecrypt\.cc/[^\s<>"\']+',
            r'https://filecrypt\.co/[^\s<>"\']+',
            r'filecrypt\.cc/Container/[A-F0-9]+\.html',
        ]
        
        all_links = []
        for pattern in patterns:
            matches = re.findall(pattern, text_content, re.IGNORECASE)
            for match in matches:
                if not match.startswith('http'):
                    match = f'https://{match}'
                if match not in all_links:
                    all_links.append(match)
        
        # Auch HTML-Links durchsuchen
        soup = BeautifulSoup(thread_response.text, 'html.parser')
        for a_tag in soup.find_all('a', href=True):
            href = a_tag.get('href')
            if 'filecrypt.cc' in href or 'filecrypt.co' in href:
                if href not in all_links:
                    all_links.append(href)
        
        print(f"    Gefundene FileCrypt-Links: {len(all_links)}")
        
        if all_links:
            print("\n    >>> ERFOLGREICH! FileCrypt-Links gefunden: <<<")
            for i, link in enumerate(all_links[:5], 1):
                print(f"      {i}. {link}")
            
            if len(all_links) > 5:
                print(f"      ... und {len(all_links) - 5} weitere")
            
            print(f"\n🎉 PROOF OF CONCEPT ERFOLGREICH!")
            print(f"   ✓ Login funktioniert")
            print(f"   ✓ {len(all_links)} FileCrypt-Links nach Login verfügbar")
            return True
        else:
            print(f"\n❌ KEINE FileCrypt-Links gefunden")
            print(f"   ✓ Login funktioniert")
            print(f"   ✗ Aber keine FileCrypt-Links sichtbar")
            
            # Debug: Speichere HTML für Analyse
            with open('thread_debug_after_login.html', 'w', encoding='utf-8') as f:
                f.write(thread_response.text)
            print(f"   📄 HTML für Debug gespeichert: thread_debug_after_login.html")
            
            return False
            
    except Exception as e:
        print(f"\n❌ FEHLER: {e}")
        return False

if __name__ == "__main__":
    success = simple_login_test()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ BEWEIS ERBRACHT: Login + FileCrypt-Extraktion funktioniert!")
    else:
        print("❌ BEWEIS FEHLGESCHLAGEN: Problem bei Login oder FileCrypt-Extraktion")
    print("=" * 60) 