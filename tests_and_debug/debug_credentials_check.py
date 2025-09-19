#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Mini-Debug für Zugangsdaten und Session

import os

def debug_credentials():
    """Debug Zugangsdaten"""
    
    print("=== ZUGANGSDATEN DEBUG ===")
    
    # Environment Variables direkt
    dl_user_env = os.environ.get('DL_USER')
    dl_password_env = os.environ.get('DL_PASSWORD')
    
    print(f"\nDirekt aus Environment:")
    print(f"  DL_USER: '{dl_user_env}'")
    print(f"  DL_PASSWORD: '{dl_password_env}'")
    print(f"  DL_USER ist None: {dl_user_env is None}")
    print(f"  DL_PASSWORD ist None: {dl_password_env is None}")
    print(f"  DL_USER ist leer: {dl_user_env == ''}")
    print(f"  DL_PASSWORD ist leer: {dl_password_env == ''}")
    
    # Mock wie in der echten Funktion
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
                        "user": dl_user_env,
                        "password": dl_password_env,
                        "cookies": ""
                    })
                }.get(section, MockConfig({})),
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            }
    
    shared_state = MockSharedState()
    
    print(f"\nÜber shared_state:")
    dl_config = shared_state.values["config"]("DL")
    user = dl_config.get("user")
    password = dl_config.get("password")
    
    print(f"  user: '{user}'")
    print(f"  password: '{password}'")
    print(f"  user ist None: {user is None}")
    print(f"  password ist None: {password is None}")
    print(f"  user ist leer: {user == ''}")
    print(f"  password ist leer: {password == ''}")
    
    print(f"\nLogin-Bedingung (not user or not password):")
    condition = not user or not password
    print(f"  Ergebnis: {condition}")
    
    if condition:
        print("  ❌ Zugangsdaten-Check würde fehlschlagen!")
    else:
        print("  ✅ Zugangsdaten-Check würde passieren!")

if __name__ == "__main__":
    debug_credentials() 