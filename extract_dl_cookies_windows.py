#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Windows Cookie-Extraktor für DL-Provider
Speziell optimiert für Windows-Systeme
"""

import os
import json
import sqlite3
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
import sys

class WindowsCookieExtractor:
    """Windows-spezifischer Cookie-Extraktor"""
    
    def __init__(self, target_domain="data-load.me"):
        self.target_domain = target_domain
        self.cookies = {}
    
    def get_windows_browser_paths(self):
        """Ermittelt Browser-Pfade auf Windows"""
        base_local = os.path.expandvars(r"%LOCALAPPDATA%")
        base_roaming = os.path.expandvars(r"%APPDATA%")
        
        return {
            'chrome': [
                os.path.join(base_local, "Google", "Chrome", "User Data", "Default", "Network", "Cookies"),
                os.path.join(base_local, "Google", "Chrome", "User Data", "Profile 1", "Network", "Cookies"),
                os.path.join(base_local, "Google", "Chrome", "User Data", "Profile 2", "Network", "Cookies"),
            ],
            'edge': [
                os.path.join(base_local, "Microsoft", "Edge", "User Data", "Default", "Network", "Cookies"),
                os.path.join(base_local, "Microsoft", "Edge", "User Data", "Profile 1", "Network", "Cookies"),
                os.path.join(base_local, "Microsoft", "Edge", "User Data", "Profile 2", "Network", "Cookies"),
            ],
            'firefox': os.path.join(base_roaming, "Mozilla", "Firefox", "Profiles"),
            'opera': [
                os.path.join(base_roaming, "Opera Software", "Opera Stable", "Cookies"),
                os.path.join(base_roaming, "Opera Software", "Opera GX Stable", "Cookies"),
            ],
            'brave': [
                os.path.join(base_local, "BraveSoftware", "Brave-Browser", "User Data", "Default", "Network", "Cookies"),
                os.path.join(base_local, "BraveSoftware", "Brave-Browser", "User Data", "Profile 1", "Network", "Cookies"),
            ]
        }
    
    def extract_chromium_cookies(self, cookie_path):
        """Extrahiert Cookies aus Chromium-basierten Browsern"""
        cookies = {}
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as temp_file:
            temp_path = temp_file.name
        
        try:
            shutil.copy2(cookie_path, temp_path)
            
            conn = sqlite3.connect(temp_path)
            cursor = conn.cursor()
            
            query = """
                SELECT name, value, host_key, path, expires_utc, is_secure, is_httponly
                FROM cookies 
                WHERE host_key LIKE ? OR host_key LIKE ?
                ORDER BY creation_utc DESC
            """
            
            cursor.execute(query, (f'%{self.target_domain}%', f'%.{self.target_domain}%'))
            
            for row in cursor.fetchall():
                name, value, host_key, path, expires_utc, is_secure, is_httponly = row
                
                cookies[name] = {
                    'value': value,
                    'domain': host_key,
                    'path': path,
                    'expires': expires_utc,
                    'secure': bool(is_secure),
                    'httponly': bool(is_httponly)
                }
            
            conn.close()
            
        finally:
            try:
                os.unlink(temp_path)
            except:
                pass
        
        return cookies
    
    def extract_firefox_cookies(self, profile_dir):
        """Extrahiert Cookies aus Firefox"""
        cookies = {}
        cookies_db = os.path.join(profile_dir, "cookies.sqlite")
        
        if not os.path.exists(cookies_db):
            return cookies
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as temp_file:
            temp_path = temp_file.name
        
        try:
            shutil.copy2(cookies_db, temp_path)
            
            conn = sqlite3.connect(temp_path)
            cursor = conn.cursor()
            
            query = """
                SELECT name, value, host, path, expiry, isSecure, isHttpOnly
                FROM moz_cookies 
                WHERE host LIKE ? OR host LIKE ?
                ORDER BY creationTime DESC
            """
            
            cursor.execute(query, (f'%{self.target_domain}%', f'%.{self.target_domain}%'))
            
            for row in cursor.fetchall():
                name, value, host, path, expiry, is_secure, is_httponly = row
                
                cookies[name] = {
                    'value': value,
                    'domain': host,
                    'path': path,
                    'expires': expiry,
                    'secure': bool(is_secure),
                    'httponly': bool(is_httponly)
                }
            
            conn.close()
            
        finally:
            try:
                os.unlink(temp_path)
            except:
                pass
        
        return cookies
    
    def extract_all_cookies(self):
        """Extrahiert Cookies von allen Windows-Browsern"""
        paths = self.get_windows_browser_paths()
        
        print("🔍 Suche nach Browser-Cookies auf Windows...")
        
        # Chromium-basierte Browser
        chromium_browsers = ['chrome', 'edge', 'opera', 'brave']
        
        for browser in chromium_browsers:
            if browser in paths:
                print(f"\n🌐 Prüfe {browser.title()}...")
                cookie_paths = paths[browser] if isinstance(paths[browser], list) else [paths[browser]]
                
                for cookie_path in cookie_paths:
                    if os.path.exists(cookie_path):
                        print(f"  ✅ Gefunden: {os.path.basename(os.path.dirname(cookie_path))}")
                        try:
                            browser_cookies = self.extract_chromium_cookies(cookie_path)
                            if browser_cookies:
                                self.cookies.update(browser_cookies)
                                print(f"  📊 {len(browser_cookies)} Cookies extrahiert")
                                return True  # Erfolgreich, stoppe bei erstem Fund
                        except Exception as e:
                            print(f"  ❌ Fehler: {e}")
                    else:
                        print(f"  ❌ Profil nicht gefunden: {os.path.basename(os.path.dirname(cookie_path))}")
        
        # Firefox
        print(f"\n🦊 Prüfe Firefox...")
        firefox_base = paths['firefox']
        
        if os.path.exists(firefox_base):
            print(f"  ✅ Firefox-Ordner gefunden")
            
            for profile_dir in os.listdir(firefox_base):
                profile_path = os.path.join(firefox_base, profile_dir)
                if os.path.isdir(profile_path):
                    print(f"  🔍 Prüfe Profil: {profile_dir}")
                    try:
                        browser_cookies = self.extract_firefox_cookies(profile_path)
                        if browser_cookies:
                            self.cookies.update(browser_cookies)
                            print(f"  📊 {len(browser_cookies)} Cookies extrahiert")
                            return True  # Erfolgreich
                    except Exception as e:
                        print(f"  ❌ Fehler: {e}")
        else:
            print(f"  ❌ Firefox nicht installiert")
        
        return len(self.cookies) > 0
    
    def save_cookies(self, output_file=None):
        """Speichert Cookies im Quasarr-Format"""
        if not self.cookies:
            print("❌ Keine Cookies gefunden!")
            return False
        
        if output_file is None:
            # Speichere auf Desktop wenn möglich
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            if os.path.exists(desktop):
                output_file = os.path.join(desktop, "dl_cookies.json")
            else:
                output_file = "dl_cookies.json"
        
        # Konvertiere zu Session-Format
        session_cookies = {}
        for name, data in self.cookies.items():
            session_cookies[name] = data['value']
        
        cookie_data = {
            'cookies': session_cookies,
            'metadata': {
                'domain': self.target_domain,
                'extracted_at': datetime.now().isoformat(),
                'total_cookies': len(session_cookies),
                'platform': 'windows',
                'cookie_details': self.cookies,
                'source': 'windows_extractor'
            }
        }
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(cookie_data, f, indent=2, ensure_ascii=False)
            
            print(f"\n✅ Cookies erfolgreich gespeichert: {os.path.abspath(output_file)}")
            print(f"📊 Insgesamt {len(session_cookies)} Cookies extrahiert")
            
            print("\n🔍 Gefundene Cookies:")
            for name in session_cookies.keys():
                expires = self.cookies[name].get('expires', 0)
                if expires > 0:
                    exp_date = datetime.fromtimestamp(expires).strftime('%Y-%m-%d')
                    print(f"  - {name} (läuft ab: {exp_date})")
                else:
                    print(f"  - {name} (Session-Cookie)")
            
            return True
            
        except Exception as e:
            print(f"❌ Fehler beim Speichern: {e}")
            return False

def main():
    print("🚀 Windows DL-Provider Cookie-Extraktor")
    print("=" * 45)
    print("💻 Speziell optimiert für Windows-Systeme")
    print()
    
    # Warnung über geschlossene Browser
    print("⚠️  WICHTIG: Schließe alle Browser bevor du fortfährst!")
    print("📌 Dies verhindert Dateisperren bei der Cookie-Extraktion")
    input("\nDrücke Enter zum Fortfahren...")
    
    extractor = WindowsCookieExtractor()
    
    # Cookie-Extraktion
    success = extractor.extract_all_cookies()
    
    if success:
        # Speichere Cookies
        if extractor.save_cookies():
            print("\n🎉 Cookie-Extraktion erfolgreich abgeschlossen!")
            print("\n📋 Nächste Schritte:")
            print("1. Kopiere 'dl_cookies.json' in dein Quasarr config-Verzeichnis")
            print("2. Starte Quasarr neu")
            print("3. Teste die DL-Integration")
            print("\n💡 Die Datei wurde auf deinem Desktop gespeichert (falls vorhanden)")
        else:
            print("\n❌ Fehler beim Speichern der Cookies")
    else:
        print(f"\n❌ Keine Cookies für {extractor.target_domain} gefunden!")
        print("\nMögliche Gründe:")
        print("- Du bist nicht bei dem DL-Provider eingeloggt")
        print("- Browser wurden noch nicht geschlossen")
        print("- Cookies wurden bereits gelöscht")
        print("- Browser verwendet andere Cookie-Speicherorte")
        
        print(f"\n💡 Tipp: Logge dich in deinem Browser bei {extractor.target_domain} ein und versuche es erneut")

if __name__ == "__main__":
    main() 