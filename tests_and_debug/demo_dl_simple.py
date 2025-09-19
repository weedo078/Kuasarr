#!/usr/bin/env python3
"""
Einfache Demo der data-load.me Integration
"""
import requests
from bs4 import BeautifulSoup
import os
import re

# Konfiguration
USERNAME = "weedo078"
PASSWORD = "zo-2!.ak"
SEARCH_QUERY = "The Last of Us S02"

def main():
    print("=== data-load.me Integration Demo ===\n")
    
    # Session erstellen
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    
    # 1. Login
    print("1. Login bei data-load.me...")
    
    # Hole CSRF Token
    login_page = session.get("https://www.data-load.me/login/")
    soup = BeautifulSoup(login_page.text, 'html.parser')
    csrf_token = soup.find('input', {'name': '_xfToken'})['value']
    
    # Login durchführen
    login_data = {
        'login': USERNAME,
        'password': PASSWORD,
        '_xfToken': csrf_token,
        '_xfRedirect': '/',
        'remember': '1'
    }
    
    resp = session.post("https://www.data-load.me/login/login", 
                       data=login_data, 
                       allow_redirects=False)
    
    if 'xf_user' in session.cookies:
        print(f"   ✓ Erfolgreich eingeloggt als {USERNAME}\n")
    else:
        print("   ✗ Login fehlgeschlagen!\n")
        return
    
    # 2. Direkt Thread öffnen (bekannte URL)
    print("2. Öffne bekannten Thread...")
    thread_url = "https://www.data-load.me/threads/the-last-of-us-s02-german-aac-1080p-web-x265-w00t.921932/"
    
    thread_resp = session.get(thread_url)
    print(f"   ✓ Thread geladen: The Last of Us S02\n")
    
    # 3. FileCrypt Links extrahieren
    print("3. Extrahiere FileCrypt Links...")
    filecrypt_links = re.findall(
        r'https?://filecrypt\.cc/Container/[A-Z0-9]+\.html', 
        thread_resp.text
    )
    
    # Duplikate entfernen
    filecrypt_links = list(set(filecrypt_links))
    
    if filecrypt_links:
        print(f"   ✓ {len(filecrypt_links)} FileCrypt Links gefunden:\n")
        for i, link in enumerate(filecrypt_links, 1):
            print(f"   {i}. {link}")
            
        print("\n4. Beispiel: Integration mit JDownloader")
        print("   Die Links können via JDownloader API hinzugefügt werden:")
        print("   - Endpoint: POST /linkgrabberv2/addLinks")
        print(f"   - Body: {{'autostart': true, 'links': '{filecrypt_links[0]}'}}")
    else:
        print("   ✗ Keine FileCrypt Links gefunden")
    
    print("\n=== Demo abgeschlossen ===")
    print("\nDie gefundenen Links können jetzt an Download-Manager")
    print("wie JDownloader weitergegeben werden.")

if __name__ == "__main__":
    main() 