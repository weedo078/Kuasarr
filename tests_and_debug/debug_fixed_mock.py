#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Debug mit komplettem Mock für shared_state

import os

def debug_complete_mock():
    """Debug mit vollständigem shared_state Mock"""
    
    print("=== VOLLSTÄNDIGER MOCK TEST ===")
    
    # Environment Variables
    dl_user_env = os.environ.get('DL_USER')
    dl_password_env = os.environ.get('DL_PASSWORD')
    
    print(f"\nCredentials: {dl_user_env} / {dl_password_env[:2]}***")
    
    # Import
    try:
        from quasarr.downloads.sources.dl import create_and_persist_session
        print("✅ Import erfolgreich")
    except ImportError as e:
        print(f"❌ Import-Fehler: {e}")
        return
    
    # VOLLSTÄNDIGER Mock
    class MockConfig:
        def __init__(self, values):
            self._values = values
        def get(self, key):
            return self._values.get(key)
    
    class MockSharedState:
        def __init__(self):
            self.storage = {}  # Für update/get
            self.values = {
                "config": lambda section: {
                    "Hostnames": MockConfig({"dl": "data-load.me"}),
                    "DL": MockConfig({
                        "user": dl_user_env,
                        "password": dl_password_env,
                        "cookies": ""
                    })
                }.get(section, MockConfig({})),
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            }
        
        def update(self, context, data):
            """Mock für shared_state.update()"""
            print(f"  Mock update(): context='{context}', data={data}")
            self.storage[context] = data
        
        def get(self, context, default=None):
            """Mock für shared_state.get()"""
            result = self.storage.get(context, default)
            print(f"  Mock get(): context='{context}', result={result}")
            return result
    
    shared_state = MockSharedState()
    
    # Test create_and_persist_session
    print(f"\n[Test] create_and_persist_session mit vollständigem Mock:")
    
    try:
        session = create_and_persist_session(shared_state)
        
        if session:
            print("  ✅ Session erfolgreich erstellt!")
            print(f"  Headers: {list(session.headers.keys())}")
            print(f"  Cookies: {len(session.cookies)} gesetzt")
            
            # Test Login durch kleine Anfrage
            try:
                response = session.get("https://data-load.me", timeout=5)
                print(f"  Test-Request Status: {response.status_code}")
                
                # Prüfe Login-Indikatoren
                login_indicators = ["logout", "abmelden", "account", "profil"]
                login_found = any(indicator in response.text.lower() for indicator in login_indicators)
                
                if login_found:
                    print("  ✅ Login erfolgreich!")
                else:
                    print("  ⚠️ Login möglicherweise fehlgeschlagen")
                    print(f"  HTML-Snippet: {response.text[:200]}...")
                    
            except Exception as req_e:
                print(f"  ⚠️ Test-Request Fehler: {req_e}")
                
        else:
            print("  ❌ Session ist None!")
            
    except Exception as e:
        print(f"  ❌ Session-Fehler: {e}")
        import traceback
        print("\nFull Traceback:")
        traceback.print_exc()

if __name__ == "__main__":
    debug_complete_mock() 