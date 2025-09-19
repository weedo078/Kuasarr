#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
import re
import sys

def test_dataload_login(username, password, hostname="data-load.me"):
    """Testet das Login bei data-load.me mit echten Credentials"""
    
    print("=== DATA-LOAD.ME LOGIN TEST ===")
    print(f"Username: {username}")
    print(f"Password: {'*' * len(password)}")
    print(f"Hostname: {hostname}")
    print()
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    session = requests.Session()
    session.headers.update(headers)
    
    try:
        print("1. Teste Verbindung zur Hauptseite...")
        response = session.get(f"https://{hostname}", timeout=10)
        print(f"   Status: {response.status_code}")
        
        print("2. Lade Login-Seite...")
        login_page = session.get(f"https://{hostname}/login/", timeout=10)
        print(f"   Status: {login_page.status_code}")
        
        if login_page.status_code != 200:
            print("❌ FEHLER: Login-Seite nicht erreichbar!")
            return False
        
        print("3. Analysiere Login-Form...")
        soup = BeautifulSoup(login_page.text, 'html.parser')
        
        # Finde die korrekte Login-Form
        login_form = None
        for form in soup.find_all("form"):
            action = form.get("action", "")
            if "/login/login" in action or action == "/login/login":
                login_form = form
                break
        
        if not login_form:
            print("❌ FEHLER: Login-Form nicht gefunden!")
            return False
        
        form_action = login_form.get("action", "/login/login")
        if form_action.startswith("/"):
            login_url = f"https://{hostname}{form_action}"
        else:
            login_url = f"https://{hostname}/{form_action}"
        
        print(f"   Login-URL: {login_url}")
        
        # Sammle alle Formularfelder
        login_data = {}
        for input_field in login_form.find_all("input"):
            name = input_field.get("name")
            if not name:
                continue
                
            input_type = input_field.get("type", "text")
            value = input_field.get("value", "")
            
            if input_type == "checkbox" and name in ["remember"]:
                value = "1"
            
            login_data[name] = value
            
            if input_type != "password":
                print(f"   Feld: {name} ({input_type}) = '{value}'")
        
        # Setze Login-Daten
        login_data["login"] = username
        login_data["password"] = password
        if "remember" in login_data:
            login_data["remember"] = "1"
        
        print("4. Sende Login-Request...")
        session.headers.update({
            "Referer": f"https://{hostname}/login/",
            "Origin": f"https://{hostname}",
            "Content-Type": "application/x-www-form-urlencoded"
        })
        
        login_response = session.post(login_url, data=login_data, timeout=10, allow_redirects=True)
        print(f"   Response Status: {login_response.status_code}")
        print(f"   Final URL: {login_response.url}")
        
        print("5. Prüfe Login-Erfolg...")
        
        # Test 1: Prüfe Startseite auf Login-Indikatoren
        home_page = session.get(f"https://{hostname}", timeout=10)
        home_text = home_page.text.lower()
        
        login_indicators = ["logout", "abmelden", "account", "profil", "benutzerkontrollzentrum"]
        login_successful = any(indicator in home_text for indicator in login_indicators)
        
        if login_successful:
            print("✅ LOGIN ERFOLGREICH - Login-Indikatoren gefunden!")
            
            # Test 2: Prüfe, ob Links sichtbar sind
            print("6. Teste Link-Sichtbarkeit...")
            test_url = f"https://{hostname}/threads/american-horror-story-s12-german-dl-1080p-web-h264-wayne.388829/"
            test_page = session.get(test_url, timeout=10)
            
            login_required_msg = "bitte anmelden oder registrieren um links zu sehen"
            if login_required_msg in test_page.text.lower():
                print("❌ PROBLEM: Links sind trotz Login nicht sichtbar!")
                return False
            else:
                print("✅ PERFEKT: Links sind sichtbar!")
                
                # Versuche FileCrypt-Links zu finden
                filecrypt_links = re.findall(r'https://filecrypt\.cc/Container/[A-Z0-9]+\.html', test_page.text)
                print(f"   Gefundene FileCrypt-Links: {len(filecrypt_links)}")
                for link in filecrypt_links[:3]:  # Zeige ersten 3
                    print(f"     - {link}")
                
                return True
        else:
            print("❌ LOGIN FEHLGESCHLAGEN - Keine Login-Indikatoren gefunden!")
            
            # Suche nach Fehlermeldungen
            error_indicators = ["fehler", "error", "incorrect", "falsch", "ungültig"]
            for indicator in error_indicators:
                if indicator in home_text:
                    print(f"   Fehlermeldung gefunden: '{indicator}'")
            
            return False
            
    except Exception as e:
        print(f"❌ EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Test mit den bereitgestellten Credentials
    username = "weedo078"
    password = "zo-2!.ak"
    hostname = "data-load.me"
    
    success = test_dataload_login(username, password, hostname)
    
    if success:
        print("\n🎉 DATA-LOAD.ME LOGIN FUNKTIONIERT! 🎉")
        sys.exit(0)
    else:
        print("\n❌ DATA-LOAD.ME LOGIN FEHLGESCHLAGEN! ❌")
        sys.exit(1) 