#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Verbose Debug für create_and_persist_session

import os
import sys

def debug_verbose_login():
    """Verbose Debug mit Mock der debug() Funktion zeigt"""
    
    print("=== VERBOSE LOGIN DEBUG ===")
    
    # Environment Variables
    dl_user_env = os.environ.get('DL_USER')
    dl_password_env = os.environ.get('DL_PASSWORD') 
    
    print(f"\nCredentials: {dl_user_env} / {dl_password_env[:2]}***")
    
    # MONKEYPATCH DEBUG FUNCTION
    original_debug = None
    
    def verbose_debug(message):
        print(f"[DEBUG] {message}")
    
    # Import und Patch
    try:
        import quasarr.downloads.sources.dl as dl_module
        
        # Patch debug function
        original_debug = getattr(dl_module, 'debug', None)
        dl_module.debug = verbose_debug
        
        print("✅ Import und Debug-Patch erfolgreich")
        
    except ImportError as e:
        print(f"❌ Import-Fehler: {e}")
        return
    
    # Vollständiger Mock
    class MockConfig:
        def __init__(self, values):
            self._values = values
        def get(self, key):
            return self._values.get(key)
    
    class MockSharedState:
        def __init__(self):
            self.storage = {}
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
            print(f"[MOCK] update(): context='{context}', data keys={list(data.keys()) if isinstance(data, dict) else type(data)}")
            self.storage[context] = data
        
        def get(self, context, default=None):
            result = self.storage.get(context, default)
            print(f"[MOCK] get(): context='{context}', result={result}")
            return result
    
    shared_state = MockSharedState()
    
    # Test create_and_persist_session mit voller Ausgabe
    print(f"\n[Test] create_and_persist_session:")
    
    try:
        session = dl_module.create_and_persist_session(shared_state)
        
        if session:
            print("  ✅ Session erfolgreich erstellt!")
            print(f"  Session-Type: {type(session)}")
            print(f"  Headers: {list(session.headers.keys())}")
            print(f"  Cookies: {len(session.cookies)} gesetzt")
        else:
            print("  ❌ Session ist None!")
            
    except Exception as e:
        print(f"  ❌ Session-Fehler: {e}")
        import traceback
        print("\nFull Traceback:")
        traceback.print_exc()
    finally:
        # Restore original debug function
        if original_debug:
            dl_module.debug = original_debug

if __name__ == "__main__":
    debug_verbose_login() 