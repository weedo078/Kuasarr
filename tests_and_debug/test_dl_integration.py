#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Test-Script für die data-load.me Integration in Quasarr

import os
import sys
import time
import argparse

# Füge den Quasarr-Pfad hinzu
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

try:
    from quasarr.search.sources.dl import dl_feed, dl_search, extract_search_id
    from quasarr.downloads.sources.dl import create_and_persist_session, get_dl_download_link
    from quasarr.providers import shared_state
    from quasarr.storage.config import Config
    print("[+] Quasarr-Module erfolgreich importiert")
except ImportError as e:
    print(f"[-] Fehler beim Importieren der Quasarr-Module: {e}")
    print("    Stelle sicher, dass du dich im Quasarr-Projektverzeichnis befindest")
    sys.exit(1)

class MockSharedState:
    """Mock-Implementierung für Shared State zu Testzwecken"""
    
    def __init__(self, dl_hostname, dl_user, dl_password):
        self.dl_hostname = dl_hostname
        self.dl_user = dl_user
        self.dl_password = dl_password
        self.session_data = {}
        
        # Mock values dict
        self.values = {
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
            "internal_address": "http://localhost:8080",
            "config": self._config
        }
    
    def _config(self, section):
        """Mock-Konfiguration"""
        if section == "Hostnames":
            return MockConfig({"dl": self.dl_hostname})
        elif section == "DL":
            return MockConfig({
                "user": self.dl_user,
                "password": self.dl_password,
                "cookies": ""
            })
        else:
            return MockConfig({})
    
    def convert_to_mb(self, size_item):
        """Konvertiert Größenangaben zu MB"""
        if not size_item or size_item.get("size", 0) == 0:
            return 0
        
        size = size_item["size"]
        unit = size_item["sizeunit"].upper()
        
        if unit == "KB":
            return size / 1024
        elif unit == "MB":
            return size
        elif unit == "GB":
            return size * 1024
        else:
            return size / (1024 * 1024)  # Assume bytes
    
    def is_imdb_id(self, search_string):
        """Prüft, ob der String eine IMDb-ID ist"""
        import re
        if re.match(r'^tt\d+$', search_string):
            return search_string
        return None
    
    def search_string_in_sanitized_title(self, search_string, title):
        """Einfacher String-Vergleich für Tests"""
        return search_string.lower() in title.lower()
    
    def update(self, key, value):
        """Speichert Session-Daten"""
        self.session_data[key] = value
    
    def get(self, key, default=None):
        """Lädt Session-Daten"""
        return self.session_data.get(key, default)

class MockConfig:
    """Mock-Konfigurationsobjekt"""
    
    def __init__(self, data):
        self.data = data
    
    def get(self, key, default=""):
        return self.data.get(key, default)
    
    def save(self, key, value):
        self.data[key] = value

def test_search_id_extraction(shared_state):
    """Testet die Such-ID-Extraktion"""
    print("\n[*] === TEST: Such-ID-Extraktion ===")
    
    import requests
    from bs4 import BeautifulSoup
    
    try:
        session = requests.Session()
        session.headers.update({
            'User-Agent': shared_state.values["user_agent"]
        })
        
        search_id = extract_search_id(session, shared_state.values["user_agent"])
        print(f"[+] Extrahierte Such-ID: {search_id}")
        return search_id
    except Exception as e:
        print(f"[-] Fehler bei Such-ID-Extraktion: {e}")
        return None

def test_dl_feed(shared_state):
    """Testet die Feed-Funktion"""
    print("\n[*] === TEST: DL Feed ===")
    
    try:
        start_time = time.time()
        results = dl_feed(shared_state, start_time, "TestClient")
        
        print(f"[+] Feed-Test abgeschlossen")
        print(f"[+] Gefundene Releases: {len(results)}")
        
        for i, result in enumerate(results[:3]):  # Zeige nur die ersten 3
            details = result.get("details", {})
            print(f"  [{i+1}] {details.get('title', 'Kein Titel')}")
            print(f"      Größe: {details.get('size', 0)} Bytes")
            print(f"      Link: {details.get('link', 'Kein Link')[:60]}...")
        
        return results
    except Exception as e:
        print(f"[-] Fehler beim Feed-Test: {e}")
        return []

def test_dl_search(shared_state, search_term):
    """Testet die Suchfunktion"""
    print(f"\n[*] === TEST: DL Suche nach '{search_term}' ===")
    
    try:
        start_time = time.time()
        results = dl_search(shared_state, start_time, "TestClient", search_term)
        
        print(f"[+] Such-Test abgeschlossen")
        print(f"[+] Gefundene Releases: {len(results)}")
        
        for i, result in enumerate(results[:5]):  # Zeige die ersten 5
            details = result.get("details", {})
            print(f"  [{i+1}] {details.get('title', 'Kein Titel')}")
            print(f"      Größe: {details.get('size', 0)} Bytes")
            print(f"      Link: {details.get('link', 'Kein Link')[:60]}...")
        
        return results
    except Exception as e:
        print(f"[-] Fehler beim Such-Test: {e}")
        return []

def test_session_creation(shared_state):
    """Testet die Session-Erstellung"""
    print("\n[*] === TEST: Session-Erstellung ===")
    
    try:
        session = create_and_persist_session(shared_state)
        
        if session:
            print("[+] Session erfolgreich erstellt")
            print(f"[+] Session-Cookies: {dict(session.cookies)}")
            return session
        else:
            print("[-] Session-Erstellung fehlgeschlagen")
            return None
    except Exception as e:
        print(f"[-] Fehler bei Session-Erstellung: {e}")
        return None

def test_download_link_extraction(shared_state, test_url):
    """Testet die Download-Link-Extraktion"""
    print(f"\n[*] === TEST: Download-Link-Extraktion ===")
    print(f"[*] Test-URL: {test_url}")
    
    try:
        filecrypt_link = get_dl_download_link(shared_state, test_url)
        
        if filecrypt_link:
            print(f"[+] FileCrypt-Link extrahiert: {filecrypt_link}")
            return filecrypt_link
        else:
            print("[-] Kein FileCrypt-Link gefunden")
            return None
    except Exception as e:
        print(f"[-] Fehler bei Download-Link-Extraktion: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description='Teste data-load.me Integration in Quasarr')
    parser.add_argument('--hostname', '-H', required=True, help='data-load.me Hostname (z.B. www.data-load.me)')
    parser.add_argument('--username', '-u', help='Benutzername für data-load.me')
    parser.add_argument('--password', '-p', help='Passwort für data-load.me')
    parser.add_argument('--search', '-s', default='test', help='Suchbegriff für Tests')
    parser.add_argument('--test-url', '-t', help='Spezifische Thread-URL für Download-Link-Test')
    parser.add_argument('--no-login', action='store_true', help='Teste ohne Login-Daten')
    
    args = parser.parse_args()
    
    # Login-Daten aus Umgebungsvariablen, falls nicht als Argument übergeben
    username = args.username or os.getenv('DL_USER') or ""
    password = args.password or os.getenv('DL_PASSWORD') or ""
    
    if not args.no_login and (not username or not password):
        print("[-] Benutzername und Passwort erforderlich!")
        print("    Verwende: --username <user> --password <pass>")
        print("    Oder setze Umgebungsvariablen: DL_USER, DL_PASSWORD")
        print("    Oder verwende --no-login für Tests ohne Anmeldung")
        return
    
    print("[*] === DATA-LOAD.ME INTEGRATION TEST ===")
    print(f"[*] Hostname: {args.hostname}")
    print(f"[*] Benutzername: {username if username else 'Nicht gesetzt'}")
    print(f"[*] Passwort: {'Gesetzt' if password else 'Nicht gesetzt'}")
    
    # Mock Shared State erstellen
    shared_state = MockSharedState(args.hostname, username, password)
    
    # Tests ausführen
    try:
        # 1. Such-ID-Extraktion testen
        search_id = test_search_id_extraction(shared_state)
        
        # 2. Session-Erstellung testen (nur bei Login-Daten)
        if not args.no_login:
            session = test_session_creation(shared_state)
        
        # 3. Feed-Test
        feed_results = test_dl_feed(shared_state)
        
        # 4. Such-Test
        search_results = test_dl_search(shared_state, args.search)
        
        # 5. Download-Link-Extraktion testen (falls URL angegeben)
        if args.test_url:
            filecrypt_link = test_download_link_extraction(shared_state, args.test_url)
        
        # Zusammenfassung
        print("\n[*] === ZUSAMMENFASSUNG ===")
        print(f"[*] Such-ID: {'Extrahiert' if search_id else 'Fehlgeschlagen'}")
        print(f"[*] Feed-Ergebnisse: {len(feed_results)}")
        print(f"[*] Such-Ergebnisse: {len(search_results)}")
        
        if feed_results or search_results:
            print("[+] Die data-load.me Integration scheint grundsätzlich zu funktionieren!")
        else:
            print("[-] Keine Ergebnisse gefunden - möglicherweise sind Anpassungen nötig")
        
    except Exception as e:
        print(f"[-] Unerwarteter Fehler: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 