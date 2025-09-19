#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
import re

def debug_dataload_login():
    """Debug-Funktion um data-load.me Login-Probleme zu diagnostizieren"""
    
    print("=== DATA-LOAD.ME LOGIN DEBUG ===")
    
    # Test-Website erreichen
    base_url = "https://data-load.me"
    login_url = f"{base_url}/login/"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36'
    }
    
    session = requests.Session()
    session.headers.update(headers)
    
    try:
        print(f"1. Teste Verbindung zu {base_url}...")
        response = session.get(base_url, timeout=10)
        print(f"   Status: {response.status_code}")
        
        print(f"2. Lade Login-Seite {login_url}...")
        login_response = session.get(login_url, timeout=10)
        print(f"   Status: {login_response.status_code}")
        
        if login_response.status_code == 200:
            print("3. Analysiere Login-Form...")
            soup = BeautifulSoup(login_response.text, 'html.parser')
            
            # Suche Login-Form
            login_form = soup.find('form')
            if login_form:
                print(f"   Form gefunden: {login_form.get('action', 'Keine Action')}")
                print(f"   Method: {login_form.get('method', 'Keine Method')}")
                
                # Alle Input-Felder anzeigen
                inputs = login_form.find_all('input')
                print(f"   Input-Felder ({len(inputs)}):")
                for inp in inputs:
                    name = inp.get('name', 'Kein Name')
                    input_type = inp.get('type', 'Kein Type')
                    value = inp.get('value', '')
                    print(f"     - {name}: {input_type} = '{value}'")
                
                # CSRF Token suchen
                csrf_token = None
                csrf_input = login_form.find('input', {'name': re.compile(r'csrf|token|_token', re.IGNORECASE)})
                if csrf_input:
                    csrf_token = csrf_input.get('value')
                    print(f"   CSRF Token gefunden: {csrf_token[:20]}...")
                else:
                    print("   KEIN CSRF Token gefunden!")
                
                # Meta CSRF Token suchen
                meta_csrf = soup.find('meta', {'name': re.compile(r'csrf|token', re.IGNORECASE)})
                if meta_csrf:
                    meta_token = meta_csrf.get('content')
                    print(f"   Meta CSRF Token: {meta_token[:20]}...")
                
            else:
                print("   KEINE Login-Form gefunden!")
                # Suche alle Forms
                all_forms = soup.find_all('form')
                print(f"   Gefundene Forms insgesamt: {len(all_forms)}")
                for i, form in enumerate(all_forms):
                    print(f"     Form {i+1}: {form.get('action', 'Keine Action')}")
        
        print("4. Teste Login mit Dummy-Daten...")
        # Dummy-Login-Versuch um Response zu sehen
        login_data = {
            'login': 'test_user',
            'password': 'test_pass'
        }
        
        login_attempt = session.post(login_url, data=login_data, timeout=10)
        print(f"   Login Response Status: {login_attempt.status_code}")
        print(f"   Response URL: {login_attempt.url}")
        
        # Suche nach Fehlermeldungen
        if "error" in login_attempt.text.lower() or "fehler" in login_attempt.text.lower():
            print("   Fehlermeldung im Response gefunden!")
        
        print("\n=== DEBUG ABGESCHLOSSEN ===")
        print("Bitte teste mit deinen echten Zugangsdaten:")
        print("Username: [dein username]")
        print("Password: [dein password]")
        
    except Exception as e:
        print(f"FEHLER beim Debug: {e}")

if __name__ == "__main__":
    debug_dataload_login() 