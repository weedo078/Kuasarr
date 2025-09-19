#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Container-Debug für data-load.me Integration

import os
import sys

def debug_container_dl():
    """Debug data-load.me direkt im Container"""
    
    print("=== CONTAINER DL DEBUG ===")
    
    # Schritt 1: Environment Variables prüfen
    print("\n[1] Environment Variables:")
    dl_user = os.environ.get('DL_USER', 'NICHT_GESETZT')
    dl_password = os.environ.get('DL_PASSWORD', 'NICHT_GESETZT')
    print(f"    DL_USER: {dl_user}")
    print(f"    DL_PASSWORD: {'***' if dl_password != 'NICHT_GESETZT' else 'NICHT_GESETZT'}")
    
    # Schritt 2: Quasarr-Module importieren
    print("\n[2] Import-Test:")
    try:
        from quasarr.downloads.sources.dl import create_and_persist_session
        from quasarr.search.sources.dl import dl_feed, dl_search
        print("    ✅ DL-Module erfolgreich importiert")
    except ImportError as e:
        print(f"    ❌ Import-Fehler: {e}")
        return
    
    # Schritt 3: Mock Shared State erstellen
    print("\n[3] Mock Shared State:")
    
    class MockConfig:
        def __init__(self, values):
            self._values = values
        def get(self, key):
            return self._values.get(key)
    
    class MockSharedState:
        def __init__(self):
            self.values = {
                "config": lambda section: {
                    "Hostnames": MockConfig({"dl": "data-load.me"}),
                    "DL": MockConfig({
                        "user": dl_user,
                        "password": dl_password,
                        "cookies": ""
                    })
                }.get(section, MockConfig({})),
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "internal_address": "http://192.168.178.76:8080"
            }
            
        def convert_to_mb(self, size_str):
            if not size_str:
                return 0
            try:
                if 'GB' in size_str.upper():
                    return float(size_str.upper().replace('GB', '').strip()) * 1024
                elif 'MB' in size_str.upper():
                    return float(size_str.upper().replace('MB', '').strip())
                else:
                    return 100  # Fallback
            except:
                return 100
    
    shared_state = MockSharedState()
    print("    ✅ Mock Shared State erstellt")
    
    # Schritt 4: Login-Session testen
    print("\n[4] Login-Session Test:")
    try:
        session = create_and_persist_session(shared_state)
        if session:
            print("    ✅ Session erfolgreich erstellt")
            print(f"    Session-Headers: {list(session.headers.keys())}")
            print(f"    Session-Cookies: {len(session.cookies)} cookies")
        else:
            print("    ❌ Session-Erstellung fehlgeschlagen")
            return
    except Exception as e:
        print(f"    ❌ Session-Fehler: {e}")
        return
    
    # Schritt 5: Feed-Test
    print("\n[5] Feed-Test:")
    try:
        import time
        start_time = time.time()
        
        results = dl_feed(shared_state, start_time, "DebugTest")
        print(f"    ✅ Feed-Funktion ausgeführt")
        print(f"    Ergebnisse: {len(results)}")
        
        if results:
            for i, result in enumerate(results[:3]):
                details = result.get("details", {})
                print(f"      [{i+1}] {details.get('title', 'Kein Titel')[:50]}...")
        else:
            print("    ⚠️ Keine Ergebnisse gefunden")
            
    except Exception as e:
        print(f"    ❌ Feed-Fehler: {e}")
        import traceback
        traceback.print_exc()
    
    # Schritt 6: Such-Test
    print("\n[6] Such-Test:")
    try:
        start_time = time.time()
        
        results = dl_search(shared_state, start_time, "DebugTest", "Matrix")
        print(f"    ✅ Such-Funktion ausgeführt")
        print(f"    Ergebnisse: {len(results)}")
        
        if results:
            for i, result in enumerate(results[:3]):
                details = result.get("details", {})
                print(f"      [{i+1}] {details.get('title', 'Kein Titel')[:50]}...")
        else:
            print("    ⚠️ Keine Such-Ergebnisse gefunden")
            
    except Exception as e:
        print(f"    ❌ Such-Fehler: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_container_dl() 