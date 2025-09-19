#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test-Script für data-load.me Login-Analyse
"""

import requests
import re
from bs4 import BeautifulSoup
import json
from urllib.parse import urljoin
import hashlib

def validate_hostname_hash(hostname):
    """Prüft ob der Hostname dem erwarteten Hash entspricht"""
    if not hostname:
        return False
    
    hostname_hash = hashlib.sha256(hostname.encode()).hexdigest()[:16]
    expected_hash = "e250f2750bcb7d82"  # Hash für data-load.me
    return hostname_hash == expected_hash

def test_dl_login(username, password):
    """Testet den Login bei data-load.me"""
    
    hostname = "data-load.me"
    
    # Hostname-Validierung
    if not validate_hostname_hash(hostname):
        print("❌ Hostname-Validierung fehlgeschlagen!")
        return False
    
    print(f"✅ Hostname-Validierung erfolgreich für {hostname}")
    
    # Session erstellen
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    })
    
    # Login-Seite laden
    login_url = f"https://{hostname}/login/"
    print(f"\n🔍 Lade Login-Seite: {login_url}")
    
    try:
        response = session.get(login_url, timeout=15)
        print(f"📄 Status Code: {response.status_code}")
        print(f"📄 Finale URL: {response.url}")
        
        if response.status_code != 200:
            print("❌ Login-Seite nicht erreichbar")
            return False
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Seitentitel anzeigen
        title = soup.title.string if soup.title else "Kein Titel"
        print(f"📄 Seitentitel: {title}")
        
        # Alle Formulare analysieren
        forms = soup.find_all('form')
        print(f"\n📋 Gefundene Formulare: {len(forms)}")
        
        login_form = None
        form_info = []
        
        for i, form in enumerate(forms):
            form_action = form.get('action', '')
            form_method = form.get('method', 'GET').upper()
            
            # Alle Input-Felder in diesem Formular
            inputs = form.find_all('input')
            input_fields = []
            
            for inp in inputs:
                field_info = {
                    'name': inp.get('name', ''),
                    'type': inp.get('type', 'text'),
                    'value': inp.get('value', ''),
                    'required': inp.get('required') is not None,
                    'placeholder': inp.get('placeholder', '')
                }
                input_fields.append(field_info)
            
            form_data = {
                'index': i,
                'action': form_action,
                'method': form_method,
                'inputs': input_fields
            }
            form_info.append(form_data)
            
            print(f"\n📝 Formular {i+1}:")
            print(f"   Action: {form_action}")
            print(f"   Method: {form_method}")
            print(f"   Input-Felder: {len(input_fields)}")
            
            for inp in input_fields:
                print(f"     - {inp['name']} ({inp['type']}): '{inp['value']}' {inp['placeholder']}")
            
            # Prüfe ob dies das Login-Formular ist
            has_login_field = any(
                field['name'].lower() in ['login', 'username', 'email', 'user'] or
                'mail' in field['name'].lower() or 'name' in field['name'].lower()
                for field in input_fields
            )
            has_password_field = any(field['type'] == 'password' for field in input_fields)
            
            if has_login_field and has_password_field:
                login_form = form
                print(f"   🎯 DIES IST DAS LOGIN-FORMULAR!")
        
        if not login_form:
            print("\n❌ Kein Login-Formular gefunden!")
            return False
        
        print(f"\n🔐 Login-Formular gefunden!")
        
        # Formular-Daten für Login vorbereiten
        form_data = {}
        
        for input_field in login_form.find_all('input'):
            name = input_field.get('name')
            if not name:
                continue
                
            value = input_field.get('value', '')
            input_type = input_field.get('type', 'text')
            
            print(f"   Feld: {name} ({input_type}) = '{value}'")
            
            # Setze Login-Credentials
            if name.lower() in ['login', 'username', 'email', 'user'] or 'mail' in name.lower():
                value = username
                print(f"     → Username gesetzt: {value}")
            elif input_type == 'password':
                value = password
                print(f"     → Passwort gesetzt: ***")
            elif input_type == 'checkbox':
                if name.lower() in ['remember', 'stay_logged_in', 'eingeloggt_bleiben']:
                    value = '1'
                    print(f"     → Checkbox aktiviert: {name}")
            elif input_type == 'hidden':
                # Behalte versteckte Felder (wichtig für CSRF-Token!)
                print(f"     → Verstecktes Feld beibehalten: {value}")
            
            form_data[name] = value
        
        print(f"\n📋 Finale Formular-Daten:")
        for key, val in form_data.items():
            display_val = "***" if "password" in key.lower() else val
            print(f"   {key}: {display_val}")
        
        # Login-Request senden
        form_action = login_form.get('action', '')
        if form_action.startswith('http'):
            submit_url = form_action
        elif form_action.startswith('/'):
            submit_url = f"https://{hostname}{form_action}"
        else:
            submit_url = urljoin(login_url, form_action) if form_action else login_url
        
        print(f"\n🚀 Sende Login-Request an: {submit_url}")
        
        # Zusätzliche Header für Login
        session.headers.update({
            'Referer': login_url,
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': f"https://{hostname}"
        })
        
        login_response = session.post(submit_url, data=form_data, timeout=15, allow_redirects=True)
        
        print(f"📡 Login-Response:")
        print(f"   Status: {login_response.status_code}")
        print(f"   URL: {login_response.url}")
        print(f"   Headers: {dict(login_response.headers)}")
        
        # Prüfe Login-Erfolg
        response_text = login_response.text.lower()
        
        # Positive Indikatoren
        success_indicators = [
            'logout', 'abmelden', 'benutzerkontrollzentrum', 
            'account', 'profil', 'dashboard', 'member'
        ]
        
        # Negative Indikatoren
        error_indicators = [
            'incorrect', 'falsch', 'ungültig', 'invalid',
            'login failed', 'anmeldung fehlgeschlagen', 'error',
            'bitte anmelden', 'please log in'
        ]
        
        found_success = [ind for ind in success_indicators if ind in response_text]
        found_errors = [ind for ind in error_indicators if ind in response_text]
        
        print(f"\n🔍 Login-Analyse:")
        print(f"   Erfolgs-Indikatoren gefunden: {found_success}")
        print(f"   Fehler-Indikatoren gefunden: {found_errors}")
        
        # Definitiver Test: Versuche Account-Seite aufzurufen
        account_url = f"https://{hostname}/account/"
        print(f"\n🧪 Teste Account-Zugriff: {account_url}")
        
        account_response = session.get(account_url, timeout=10)
        print(f"   Account-Seite Status: {account_response.status_code}")
        print(f"   Account-Seite URL: {account_response.url}")
        
        account_content = account_response.text.lower()
        account_success = any(ind in account_content for ind in success_indicators)
        account_error = any(ind in account_content for ind in error_indicators)
        
        print(f"   Account-Zugriff erfolgreich: {account_success}")
        print(f"   Account-Zugriff Fehler: {account_error}")
        
        # Endgültiges Ergebnis
        if found_success and not found_errors and account_success:
            print(f"\n✅ LOGIN ERFOLGREICH!")
            return True
        elif found_errors or account_error:
            print(f"\n❌ LOGIN FEHLGESCHLAGEN - Credentials falsch")
            return False
        else:
            print(f"\n⚠️ LOGIN-STATUS UNKLAR - manuelle Prüfung erforderlich")
            return None
            
    except Exception as e:
        print(f"\n💥 Fehler beim Login-Test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import os
    
    # Credentials aus Umgebungsvariablen
    username = os.environ.get("DL_USER", "").strip()
    password = os.environ.get("DL_PASSWORD", "").strip()
    
    if not username or not password:
        print("❌ Keine Credentials gesetzt!")
        print("Setze DL_USER und DL_PASSWORD Umgebungsvariablen")
        exit(1)
    
    print(f"🧪 Teste Login für Benutzer: {username}")
    result = test_dl_login(username, password)
    
    if result is True:
        print(f"\n🎉 Test erfolgreich! Login funktioniert.")
    elif result is False:
        print(f"\n💀 Test fehlgeschlagen! Login funktioniert nicht.")
    else:
        print(f"\n🤔 Test unschlüssig! Manuelle Prüfung erforderlich.") 