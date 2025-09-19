#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# KORRIGIERTER Login-Test basierend auf Form-Analyse

import requests
from bs4 import BeautifulSoup
import re
import time

# Test-Credentials
USERNAME = "weedo078"
PASSWORD = "monEY125\""
HOST = "www.data-load.me"

def corrected_login_test():
    """Korrigierter Login-Test mit richtigen Form-Feldern"""
    
    print("=" * 60)
    print("KORRIGIERTER LOGIN-TEST")
    print("=" * 60)
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36'
    })
    
    try:
        # SCHRITT 1: Login-Seite laden
        print("\n[1] Lade Login-Seite...")
        response = session.get(f"https://{HOST}/login/", timeout=15)
        print(f"    Status: {response.status_code}")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # SCHRITT 2: Login-Form finden (Formular 2 basierend auf Analyse)
        print("\n[2] Analysiere Login-Form...")
        
        login_form = None
        forms = soup.find_all('form')
        
        for form in forms:
            if form.get('action') == '/login/login':
                login_form = form
                break
        
        if not login_form:
            print("    [!] Kein Login-Formular gefunden")
            return False
        
        print(f"    Login-Form gefunden: {login_form.get('action')}")
        
        # SCHRITT 3: Alle Form-Daten sammeln
        form_data = {}
        
        for inp in login_form.find_all('input'):
            name = inp.get('name')
            value = inp.get('value', '')
            input_type = inp.get('type', 'text')
            
            if name:  # Nur benannte Felder
                form_data[name] = value
                print(f"    Feld gefunden: {name} = '{value}' (type: {input_type})")
            elif input_type == 'checkbox':
                # Unnamed checkbox - lass es weg oder setze Standard
                print(f"    Unnamed checkbox ignoriert (type: {input_type})")
        
        # SCHRITT 4: Login-Daten setzen
        form_data['login'] = USERNAME
        form_data['password'] = PASSWORD
        form_data['remember'] = '1'  # Remember me
        
        print(f"\n[3] Finale Login-Daten:")
        for key, value in form_data.items():
            if key == 'password':
                print(f"    {key}: ***")
            elif '_xfToken' in key:
                print(f"    {key}: {value[:30]}...")
            else:
                print(f"    {key}: {value}")
        
        # SCHRITT 5: Login durchführen
        print(f"\n[4] Sende Login-Request...")
        
        session.headers.update({
            'Referer': f'https://{HOST}/login/',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': f'https://{HOST}'
        })
        
        login_response = session.post(f"https://{HOST}/login/login", data=form_data, timeout=15, allow_redirects=True)
        
        print(f"    Status: {login_response.status_code}")
        print(f"    Final URL: {login_response.url}")
        
        # SCHRITT 6: Login-Erfolg prüfen (detaillierter)
        print(f"\n[5] Prüfe Login-Status...")
        
        response_text = login_response.text.lower()
        
        # Speichere Response für Debug
        with open('login_response_debug.html', 'w', encoding='utf-8') as f:
            f.write(login_response.text)
        print(f"    Login-Response gespeichert: login_response_debug.html")
        
        # Verschiedene Erfolgsindikatoren
        checks = {
            'Username im Text': USERNAME.lower() in response_text,
            'Logout vorhanden': 'logout' in response_text,
            'Abmelden vorhanden': 'abmelden' in response_text,
            'Account/Konto': any(word in response_text for word in ['account', 'konto', 'profil']),
            'Kein Login in URL': 'login' not in login_response.url.lower(),
            'Startseite erreicht': login_response.url.lower() in [f'https://{HOST}/', f'https://{HOST}'],
            'Keine Fehlermeldung': not any(word in response_text for word in ['error', 'fehler', 'ungültig', 'invalid'])
        }
        
        print(f"    Detaillierte Login-Prüfung:")
        success_count = 0
        for check, result in checks.items():
            status = "✓" if result else "✗"
            print(f"      {status} {check}: {result}")
            if result:
                success_count += 1
        
        login_successful = success_count >= 3  # Mindestens 3 von 7 Checks
        print(f"\n    >>> LOGIN {'ERFOLGREICH' if login_successful else 'FEHLGESCHLAGEN'} ({success_count}/7 Checks) <<<")
        
        if not login_successful:
            # Prüfe auf spezifische Fehlermeldungen
            print(f"\n    Suche nach Fehlermeldungen...")
            
            error_soup = BeautifulSoup(login_response.text, 'html.parser')
            error_elements = error_soup.find_all(['div', 'span', 'p'], class_=lambda x: x and any(word in str(x).lower() for word in ['error', 'message', 'alert']))
            
            for elem in error_elements:
                text = elem.get_text(strip=True)
                if text and len(text) > 5:
                    print(f"      Mögliche Fehlermeldung: {text}")
            
            return False
        
        # SCHRITT 7: Thread-Seite nach Login testen
        print(f"\n[6] Teste Thread-Zugriff nach erfolgreichem Login...")
        
        # Reset Content-Type
        session.headers['Content-Type'] = 'text/html'
        
        thread_url = "https://www.data-load.me/threads/the-last-of-us-s02-german-aac-1080p-web-x265-w00t.921932/"
        print(f"    Thread-URL: {thread_url}")
        
        thread_response = session.get(thread_url, timeout=15)
        print(f"    Thread-Status: {thread_response.status_code}")
        
        # SCHRITT 8: FileCrypt-Links extrahieren
        print(f"\n[7] Extrahiere FileCrypt-Links...")
        
        # Text-basierte Suche
        text_content = thread_response.text
        
        patterns = [
            r'https://filecrypt\.cc/[^\s<>"\']+',
            r'https://filecrypt\.co/[^\s<>"\']+',
            r'filecrypt\.cc/Container/[A-F0-9]+\.html',
        ]
        
        filecrypt_links = []
        
        for pattern in patterns:
            matches = re.findall(pattern, text_content, re.IGNORECASE)
            for match in matches:
                if not match.startswith('http'):
                    match = f'https://{match}'
                if match not in filecrypt_links:
                    filecrypt_links.append(match)
        
        # HTML-Element-basierte Suche
        thread_soup = BeautifulSoup(thread_response.text, 'html.parser')
        for a_tag in thread_soup.find_all('a', href=True):
            href = a_tag.get('href')
            if 'filecrypt.cc' in href or 'filecrypt.co' in href:
                if href not in filecrypt_links:
                    filecrypt_links.append(href)
        
        print(f"    Gefundene FileCrypt-Links: {len(filecrypt_links)}")
        
        # Speichere Thread-HTML für Debug
        with open('thread_after_login_debug.html', 'w', encoding='utf-8') as f:
            f.write(thread_response.text)
        print(f"    Thread-HTML gespeichert: thread_after_login_debug.html")
        
        if filecrypt_links:
            print(f"\n🎉 ERFOLGREICH! FileCrypt-Links nach Login gefunden:")
            for i, link in enumerate(filecrypt_links[:5], 1):
                print(f"      {i}. {link}")
            
            if len(filecrypt_links) > 5:
                print(f"      ... und {len(filecrypt_links) - 5} weitere")
            
            print(f"\n✅ BEWEIS ERBRACHT:")
            print(f"   ✓ Login funktioniert")
            print(f"   ✓ {len(filecrypt_links)} FileCrypt-Links verfügbar")
            return True
        else:
            print(f"\n⚠️ TEILWEISE ERFOLGREICH:")
            print(f"   ✓ Login funktioniert")
            print(f"   ✗ Keine FileCrypt-Links gefunden")
            print(f"   📄 Prüfe die gespeicherten HTML-Dateien für weitere Analyse")
            return False
            
    except Exception as e:
        print(f"\n❌ FEHLER: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = corrected_login_test()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ VOLLSTÄNDIGER NACHWEIS ERBRACHT!")
        print("   Login UND FileCrypt-Extraktion funktionieren!")
    else:
        print("⚠️ TEILWEISE ERFOLGREICH oder FEHLGESCHLAGEN")
        print("   Prüfe die Debug-Dateien für weitere Informationen")
    print("=" * 60) 