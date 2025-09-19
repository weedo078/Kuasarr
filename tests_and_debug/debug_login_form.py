#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Debug Login-Form Struktur

import requests
from bs4 import BeautifulSoup

def analyze_login_form():
    """Analysiere die Login-Form-Struktur"""
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36'
    })
    
    try:
        print("=== LOGIN-FORM ANALYSE ===")
        
        # Login-Seite laden
        response = session.get("https://www.data-load.me/login/", timeout=10)
        print(f"Status: {response.status_code}")
        
        # HTML speichern
        with open('login_page_debug.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
        print("Login-Seite gespeichert: login_page_debug.html")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Alle Formulare finden
        forms = soup.find_all('form')
        print(f"\nGefundene Formulare: {len(forms)}")
        
        for i, form in enumerate(forms):
            print(f"\n--- FORMULAR {i+1} ---")
            print(f"Action: {form.get('action')}")
            print(f"Method: {form.get('method')}")
            print(f"Class: {form.get('class')}")
            
            # Alle Input-Felder
            inputs = form.find_all('input')
            print(f"Input-Felder: {len(inputs)}")
            
            for inp in inputs:
                name = inp.get('name')
                type_attr = inp.get('type')
                value = inp.get('value', '')
                placeholder = inp.get('placeholder', '')
                
                print(f"  - {name}: type={type_attr}, value='{value}', placeholder='{placeholder}'")
        
        # Suche spezifisch nach Login-Feldern
        print(f"\n=== SPEZIFISCHE FELDER ===")
        
        # Username/Email Feld
        username_fields = soup.find_all('input', {'type': ['text', 'email']})
        print(f"Username/Email Felder: {len(username_fields)}")
        for field in username_fields:
            print(f"  - Name: {field.get('name')}, Placeholder: {field.get('placeholder')}")
        
        # Password Feld
        password_fields = soup.find_all('input', {'type': 'password'})
        print(f"Passwort Felder: {len(password_fields)}")
        for field in password_fields:
            print(f"  - Name: {field.get('name')}, Placeholder: {field.get('placeholder')}")
        
        # Token Felder
        token_fields = soup.find_all('input', {'name': lambda x: x and 'token' in x.lower()})
        csrf_fields = soup.find_all('input', {'name': lambda x: x and 'csrf' in x.lower()})
        xf_fields = soup.find_all('input', {'name': lambda x: x and 'xf' in x.lower()})
        
        print(f"Token-ähnliche Felder: {len(token_fields + csrf_fields + xf_fields)}")
        for field in token_fields + csrf_fields + xf_fields:
            print(f"  - Name: {field.get('name')}, Value: {field.get('value', '')[:30]}...")
        
        # Prüfe HTML data-csrf
        html_tag = soup.find('html')
        if html_tag:
            csrf_attr = html_tag.get('data-csrf')
            if csrf_attr:
                print(f"HTML data-csrf: {csrf_attr[:30]}...")
        
        return True
        
    except Exception as e:
        print(f"Fehler: {e}")
        return False

if __name__ == "__main__":
    analyze_login_form() 