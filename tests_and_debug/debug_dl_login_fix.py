#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
import re
import json

def debug_dataload_login_complete():
    """Umfassende Analyse der data-load.me Login-Mechanismen"""
    
    print("=== VOLLSTÄNDIGE DATA-LOAD.ME LOGIN ANALYSE ===")
    
    base_url = "https://data-load.me"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36'
    }
    
    session = requests.Session()
    session.headers.update(headers)
    
    try:
        # 1. Teste verschiedene Login-URLs
        login_urls = [
            f"{base_url}/login/",
            f"{base_url}/login",
            f"{base_url}/signin/",
            f"{base_url}/signin",
            f"{base_url}/auth/",
            f"{base_url}/members/",
        ]
        
        print("1. Teste verschiedene Login-URLs...")
        valid_urls = []
        for url in login_urls:
            try:
                response = session.get(url, timeout=5)
                print(f"   {url}: {response.status_code}")
                if response.status_code == 200:
                    valid_urls.append((url, response))
            except:
                print(f"   {url}: FEHLER")
        
        # 2. Analysiere alle gefundenen Login-Seiten
        for url, response in valid_urls:
            print(f"\n2. Analysiere {url}...")
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Suche alle Forms
            all_forms = soup.find_all('form')
            print(f"   Gefundene Forms: {len(all_forms)}")
            
            for i, form in enumerate(all_forms):
                action = form.get('action', 'Keine Action')
                method = form.get('method', 'get')
                print(f"   Form {i+1}: {method.upper()} -> {action}")
                
                # Suche nach Login-relevanten Inputs
                inputs = form.find_all('input')
                login_fields = []
                for inp in inputs:
                    name = inp.get('name', '')
                    input_type = inp.get('type', '')
                    if any(keyword in name.lower() for keyword in ['login', 'user', 'email', 'pass']):
                        login_fields.append(f"{name} ({input_type})")
                
                if login_fields:
                    print(f"     LOGIN-RELEVANTE FELDER: {', '.join(login_fields)}")
                
                # Zeige alle Input-Felder der Form
                if any(keyword in action.lower() for keyword in ['login', 'signin', 'auth']):
                    print(f"     ALLE FELDER:")
                    for inp in inputs:
                        name = inp.get('name', 'Kein Name')
                        input_type = inp.get('type', 'text')
                        value = inp.get('value', '')
                        print(f"       - {name}: {input_type} = '{value}'")
        
        # 3. Suche nach Login-Links/Buttons
        print(f"\n3. Suche Login-Links auf Hauptseite...")
        main_response = session.get(base_url, timeout=10)
        main_soup = BeautifulSoup(main_response.text, 'html.parser')
        
        # Suche Links mit Login-Keywords
        login_links = []
        for link in main_soup.find_all('a', href=True):
            href = link.get('href')
            text = link.get_text().strip().lower()
            if any(keyword in text for keyword in ['login', 'anmelden', 'sign in', 'einloggen']):
                login_links.append((text, href))
        
        print(f"   Gefundene Login-Links: {len(login_links)}")
        for text, href in login_links:
            print(f"     - '{text}' -> {href}")
        
        # 4. Suche nach JavaScript Login-Mechanismen
        print(f"\n4. Suche JavaScript Login-Mechanismen...")
        scripts = main_soup.find_all('script')
        js_login_found = False
        for script in scripts:
            if script.string:
                if any(keyword in script.string.lower() for keyword in ['login', 'signin', 'authenticate']):
                    js_login_found = True
                    print("     JavaScript Login-Code gefunden!")
        
        if not js_login_found:
            print("     Kein JavaScript Login-Code gefunden.")
        
        print("\n=== ANALYSE ABGESCHLOSSEN ===")
        
    except Exception as e:
        print(f"FEHLER beim Debug: {e}")

if __name__ == "__main__":
    debug_dataload_login_complete() 