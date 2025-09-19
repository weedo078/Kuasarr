#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Detailliertes Debug für Login-Session-Problem

import os
import sys

def debug_login_session():
    """Detailliertes Debug der Login-Session"""
    
    print("=== DETAILLIERTES LOGIN DEBUG ===")
    
    # Environment Variables
    dl_user = os.environ.get('DL_USER', 'NICHT_GESETZT')
    dl_password = os.environ.get('DL_PASSWORD', 'NICHT_GESETZT')
    
    print(f"\nCredentials:")
    print(f"  DL_USER: {dl_user}")
    print(f"  DL_PASSWORD: {dl_password[:2]}***{dl_password[-2:] if len(dl_password) > 4 else '***'}")
    
    # Import test
    try:
        from quasarr.downloads.sources.dl import create_and_persist_session
        print("\n✅ Import erfolgreich")
    except ImportError as e:
        print(f"\n❌ Import-Fehler: {e}")
        return
    
    # Minimaler Mock - nur was create_and_persist_session braucht
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
            }
    
    shared_state = MockSharedState()
    
    # Test was create_and_persist_session erwartet
    print("\n[Test] Shared State Zugriffe:")
    try:
        hostnames = shared_state.values["config"]("Hostnames")
        dl_hostname = hostnames.get("dl")
        print(f"  DL Hostname: {dl_hostname}")
        
        dl_config = shared_state.values["config"]("DL")
        user = dl_config.get("user")
        password = dl_config.get("password")
        cookies = dl_config.get("cookies")
        
        print(f"  DL User: {user}")
        print(f"  DL Password: {password[:2] if password else 'None'}***")
        print(f"  DL Cookies: {cookies}")
        
    except Exception as e:
        print(f"  ❌ Zugriffs-Fehler: {e}")
        return
    
    # Jetzt versuche create_and_persist_session mit Fehler-Details
    print("\n[Test] create_and_persist_session:")
    try:
        session = create_and_persist_session(shared_state)
        if session:
            print("  ✅ Session erfolgreich erstellt!")
            print(f"  Headers: {list(session.headers.keys())}")
            print(f"  Cookies: {len(session.cookies)} gesetzt")
            
            # Test eine einfache Anfrage
            try:
                response = session.get("https://data-load.me", timeout=5)
                print(f"  Test-Request Status: {response.status_code}")
                if 'data-logged-in="true"' in response.text:
                    print("  ✅ Login erfolgreich!")
                else:
                    print("  ⚠️ Login möglicherweise fehlgeschlagen")
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
    debug_login_session() 