#!/usr/bin/env python3
"""
Schritt-für-Schritt Test des data-load.me Logins
"""
import requests
from bs4 import BeautifulSoup
import time
import sys

# Credentials
USERNAME = "weedo078"
PASSWORD = 'zo-2!.ak'
LOGIN_URL = "https://www.data-load.me/login/login"
THREAD_URL = "https://www.data-load.me/threads/the-last-of-us-s02-german-aac-1080p-web-x265-w00t.921932/"

def main():
    print("=== data-load.me Login Test ===\n")
    
    # Session erstellen
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'de-DE,de;q=0.9,en;q=0.8',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    })
    
    print("1. Hole Login-Seite...")
    try:
        resp = session.get("https://www.data-load.me/login/", timeout=30)
        print(f"   Status: {resp.status_code}")
        print(f"   Cookies erhalten: {list(resp.cookies.keys())}")
        
        # Speichere HTML zur Analyse
        with open('login_page.html', 'w', encoding='utf-8') as f:
            f.write(resp.text)
        print("   HTML gespeichert als login_page.html")
        
        # CSRF Token extrahieren - verschiedene Methoden
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # Methode 1: Standard XenForo Token
        csrf_input = soup.find('input', {'name': '_xfToken'})
        if csrf_input:
            csrf_token = csrf_input.get('value', '')
            print(f"   ✓ CSRF Token gefunden: {csrf_token[:20]}...")
        else:
            # Methode 2: Alternative Namen
            for name in ['csrf', 'token', 'csrf_token', '_token']:
                csrf_input = soup.find('input', {'name': name})
                if csrf_input:
                    csrf_token = csrf_input.get('value', '')
                    print(f"   ✓ CSRF Token gefunden ({name}): {csrf_token[:20]}...")
                    break
            else:
                # Methode 3: Suche alle hidden inputs
                print("   Suche alle hidden inputs:")
                hidden_inputs = soup.find_all('input', {'type': 'hidden'})
                for inp in hidden_inputs:
                    print(f"     - {inp.get('name', 'unnamed')}: {inp.get('value', '')[:30]}...")
                    
                if not hidden_inputs:
                    print("   FEHLER: Keine hidden inputs gefunden!")
                    
                # Debug: Suche Login-Form
                login_form = soup.find('form', {'action': lambda x: x and 'login' in x})
                if login_form:
                    print("   Login-Form gefunden!")
                else:
                    print("   WARNUNG: Kein Login-Form gefunden!")
                return
        
    except Exception as e:
        print(f"   FEHLER beim Abrufen der Login-Seite: {e}")
        return
    
    print("\n2. Sende Login-Daten...")
    login_data = {
        'login': USERNAME,
        'password': PASSWORD,
        '_xfToken': csrf_token,
        '_xfRedirect': '/',
        'remember': '1'
    }
    
    print("   Login-Daten:")
    for key, value in login_data.items():
        if key == 'password':
            print(f"     {key}: {'*' * len(value)}")
        elif key == '_xfToken':
            print(f"     {key}: {value[:20]}...")
        else:
            print(f"     {key}: {value}")
    
    try:
        resp = session.post(LOGIN_URL, data=login_data, timeout=30, allow_redirects=False)
        print(f"   Status: {resp.status_code}")
        print(f"   Location Header: {resp.headers.get('Location', 'Keine')}")
        print(f"   Neue Cookies: {list(resp.cookies.keys())}")
        
        # Speichere Login-Response
        with open('login_response.html', 'w', encoding='utf-8') as f:
            f.write(resp.text)
        print("   Login-Response gespeichert als login_response.html")
        
        # Prüfe Response auf Fehler
        if 'error' in resp.text.lower() or 'fehler' in resp.text.lower():
            print("   ✗ Möglicher Fehler in der Response gefunden!")
            soup = BeautifulSoup(resp.text, 'html.parser')
            # Suche nach Fehlermeldungen
            for error_class in ['errorOverlay', 'error', 'alert', 'message']:
                error_elem = soup.find(class_=error_class)
                if error_elem:
                    print(f"   Fehlermeldung: {error_elem.get_text(strip=True)[:100]}...")
        
        # Prüfe auf Session-Cookie
        if 'xf_user' in session.cookies:
            print(f"   ✓ Session Cookie erhalten: xf_user={session.cookies['xf_user'][:20]}...")
        else:
            print("   ✗ Kein Session Cookie erhalten - Login fehlgeschlagen?")
            print(f"   Alle Session-Cookies: {list(session.cookies.keys())}")
            
    except Exception as e:
        print(f"   FEHLER beim Login: {e}")
        return
    
    print("\n3. Teste Login-Status auf Hauptseite...")
    try:
        resp = session.get("https://www.data-load.me/", timeout=30)
        print(f"   Status: {resp.status_code}")
        
        # Prüfe ob eingeloggt
        if USERNAME in resp.text:
            print(f"   ✓ Erfolgreich eingeloggt als {USERNAME}")
        else:
            print("   ✗ Username nicht gefunden - Login fehlgeschlagen?")
            
        # Suche nach Login/Logout Links
        soup = BeautifulSoup(resp.text, 'html.parser')
        if soup.find('a', {'href': lambda x: x and '/logout/' in x}):
            print("   ✓ Logout-Link gefunden - definitiv eingeloggt!")
        else:
            print("   ✗ Kein Logout-Link gefunden")
            
    except Exception as e:
        print(f"   FEHLER beim Prüfen des Login-Status: {e}")
        return
    
    print("\n4. Rufe Thread-Seite ab...")
    try:
        resp = session.get(THREAD_URL, timeout=30)
        print(f"   Status: {resp.status_code}")
        
        # Suche nach FileCrypt Links
        if 'filecrypt.cc' in resp.text:
            print("   ✓ FileCrypt Links gefunden!")
            
            # Extrahiere Links
            soup = BeautifulSoup(resp.text, 'html.parser')
            filecrypt_links = []
            
            # Methode 1: Direkte Links
            for link in soup.find_all('a', href=lambda x: x and 'filecrypt.cc' in x):
                filecrypt_links.append(link['href'])
                
            # Methode 2: In Text/Code Blöcken
            for elem in soup.find_all(['code', 'pre', 'div']):
                if elem.text and 'filecrypt.cc' in elem.text:
                    import re
                    links = re.findall(r'https?://filecrypt\.cc/Container/[A-Z0-9]+\.html', elem.text)
                    filecrypt_links.extend(links)
            
            # Duplikate entfernen
            filecrypt_links = list(set(filecrypt_links))
            
            print(f"   Gefundene Links: {len(filecrypt_links)}")
            for i, link in enumerate(filecrypt_links[:5], 1):
                print(f"   {i}. {link}")
                
        else:
            print("   ✗ Keine FileCrypt Links gefunden")
            print("   Prüfe ob Login wirklich erfolgreich war...")
            
            # Debug: Speichere HTML
            with open('thread_response.html', 'w', encoding='utf-8') as f:
                f.write(resp.text)
            print("   HTML gespeichert als thread_response.html zur Analyse")
            
    except Exception as e:
        print(f"   FEHLER beim Abrufen der Thread-Seite: {e}")
        
    print("\n=== Test abgeschlossen ===")

if __name__ == "__main__":
    main() 