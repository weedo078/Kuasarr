#!/usr/bin/env python3
"""
Schnelles Demo für data-load.me Integration
"""

import requests
from bs4 import BeautifulSoup
import re
import os

# Setze Umgebungsvariablen für Test
os.environ['DL_USER'] = 'weedo078'
os.environ['DL_PASSWORD'] = 'zo-2!.ak'

def quick_test():
    print("=== SCHNELLER data-load.me TEST ===\n")
    
    user = os.environ.get('DL_USER')
    password = os.environ.get('DL_PASSWORD')
    
    print(f"🔐 Teste Login für: {user}")
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    
    try:
        # 1. Lade Startseite
        print("1. Lade Startseite...")
        response = session.get("https://data-load.me", timeout=10)
        print(f"   Status: {response.status_code}")
        
        # 2. Lade Login-Seite
        print("2. Lade Login-Seite...")
        login_page = session.get("https://data-load.me/login/", timeout=10)
        print(f"   Status: {login_page.status_code}")
        
        # 3. Parse Login-Form
        soup = BeautifulSoup(login_page.text, 'html.parser')
        
        # Finde Login-Form
        forms = soup.find_all('form')
        print(f"   Gefundene Forms: {len(forms)}")
        
        for i, form in enumerate(forms):
            action = form.get('action', 'keine')
            print(f"   Form {i+1}: Action = {action}")
            
            inputs = form.find_all('input')
            for inp in inputs:
                name = inp.get('name', 'kein-name')
                typ = inp.get('type', 'text')
                print(f"     Input: {name} ({typ})")
        
        # Versuche Login mit erstem passenden Form
        login_form = None
        for form in forms:
            if form.find('input', {'name': 'login'}) or form.find('input', {'name': 'email'}):
                login_form = form
                break
        
        if login_form:
            print("3. Versuche Login...")
            
            # Sammle Form-Daten
            login_data = {}
            for inp in login_form.find_all('input'):
                name = inp.get('name')
                if name:
                    value = inp.get('value', '')
                    login_data[name] = value
            
            # Setze Login-Daten
            if 'login' in login_data:
                login_data['login'] = user
            if 'email' in login_data:
                login_data['email'] = user
            if 'password' in login_data:
                login_data['password'] = password
            
            action = login_form.get('action', '/login/login')
            if not action.startswith('http'):
                login_url = f"https://data-load.me{action}"
            else:
                login_url = action
            
            print(f"   Login-URL: {login_url}")
            print(f"   Login-Daten: {list(login_data.keys())}")
            
            # Sende Login
            login_response = session.post(login_url, data=login_data, timeout=10)
            print(f"   Login Response: {login_response.status_code}")
            print(f"   Redirect URL: {login_response.url}")
            
            # Prüfe Erfolg
            if "login" not in login_response.url.lower():
                print("   ✅ Login vermutlich erfolgreich!")
                
                # 4. Teste Suche
                print("4. Teste Suche nach 'Matrix'...")
                search_urls = [
                    "https://data-load.me/search/35741395/?q=Matrix&o=relevance",
                    "https://data-load.me/search/35741395/?q=Matrix&o=date",
                    "https://data-load.me/search/?q=Matrix",
                ]
                
                for search_url in search_urls:
                    try:
                        print(f"   Teste: {search_url}")
                        search_response = session.get(search_url, timeout=10)
                        print(f"   Status: {search_response.status_code}")
                        
                        if search_response.status_code == 200:
                            # Parse Ergebnisse
                            soup = BeautifulSoup(search_response.text, 'html.parser')
                            
                            # Suche nach Links
                            links = soup.find_all('a', href=True)
                            thread_links = []
                            
                            for link in links:
                                href = link.get('href', '')
                                text = link.get_text(strip=True)
                                
                                if (('thread' in href.lower() or 'topic' in href.lower()) and 
                                    text and len(text) > 10):
                                    thread_links.append((text, href))
                            
                            print(f"   Gefundene Thread-Links: {len(thread_links)}")
                            
                            for i, (title, url) in enumerate(thread_links[:3]):
                                print(f"   {i+1}. {title[:50]}...")
                                print(f"      URL: {url}")
                            
                            if thread_links:
                                print("   ✅ Suchergebnisse gefunden!")
                                break
                            else:
                                print("   ⚠️ Keine Thread-Links gefunden")
                        
                    except Exception as e:
                        print(f"   ❌ Fehler bei {search_url}: {e}")
                
            else:
                print("   ❌ Login fehlgeschlagen")
                print(f"   Response Text Preview: {login_response.text[:200]}...")
        
        else:
            print("❌ Kein Login-Form gefunden")
    
    except Exception as e:
        print(f"❌ Fehler: {e}")
    
    print("\n=== TEST ABGESCHLOSSEN ===")

if __name__ == "__main__":
    quick_test() 