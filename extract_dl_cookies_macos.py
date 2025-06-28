#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
macOS Cookie-Extraktor für DL-Provider
Speziell optimiert für macOS-Systeme
"""

import os
import json
import sqlite3
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
import sys
import plistlib

class MacOSCookieExtractor:
    """macOS-spezifischer Cookie-Extraktor"""
    
    def __init__(self, target_domain="data-load.me"):
        self.target_domain = target_domain
        self.cookies = {}
    
    def get_macos_browser_paths(self):
        """Ermittelt Browser-Pfade auf macOS"""
        home = os.path.expanduser("~")
        
        return {
            'chrome': [
                os.path.join(home, "Library", "Application Support", "Google", "Chrome", "Default", "Cookies"),
                os.path.join(home, "Library", "Application Support", "Google", "Chrome", "Profile 1", "Cookies"),
                os.path.join(home, "Library", "Application Support", "Google", "Chrome", "Profile 2", "Cookies"),
            ],
            'edge': [
                os.path.join(home, "Library", "Application Support", "Microsoft Edge", "Default", "Cookies"),
                os.path.join(home, "Library", "Application Support", "Microsoft Edge", "Profile 1", "Cookies"),
                os.path.join(home, "Library", "Application Support", "Microsoft Edge", "Profile 2", "Cookies"),
            ],
            'firefox': os.path.join(home, "Library", "Application Support", "Firefox", "Profiles"),
            'safari': os.path.join(home, "Library", "Cookies", "Cookies.binarycookies"),
            'brave': [
                os.path.join(home, "Library", "Application Support", "BraveSoftware", "Brave-Browser", "Default", "Cookies"),
                os.path.join(home, "Library", "Application Support", "BraveSoftware", "Brave-Browser", "Profile 1", "Cookies"),
            ],
            'vivaldi': [
                os.path.join(home, "Library", "Application Support", "Vivaldi", "Default", "Cookies"),
                os.path.join(home, "Library", "Application Support", "Vivaldi", "Profile 1", "Cookies"),
            ],
            'opera': [
                os.path.join(home, "Library", "Application Support", "com.operasoftware.Opera", "Cookies"),
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
    
    def extract_safari_cookies(self, cookies_path):
        """Extrahiert Cookies aus Safari (vereinfacht)"""
        cookies = {}
        
        # Safari verwendet ein binäres Format, das schwer zu parsen ist
        # Hier implementieren wir eine vereinfachte Variante
        try:
            # Für Safari empfehlen wir die Verwendung eines anderen Browsers
            # oder manuelle Cookie-Extraktion
            print("  ⚠️  Safari-Cookie-Extraktion nicht implementiert")
            print("      Tipp: Nutze Chrome, Firefox oder Edge für einfachere Extraktion")
        except Exception as e:
            print(f"  ❌ Safari-Fehler: {e}")
        
        return cookies
    
    def extract_all_cookies(self):
        """Extrahiert Cookies von allen macOS-Browsern"""
        paths = self.get_macos_browser_paths()
        
        print("🔍 Suche nach Browser-Cookies auf macOS...")
        
        # Chromium-basierte Browser
        chromium_browsers = ['chrome', 'edge', 'brave', 'vivaldi', 'opera']
        
        for browser in chromium_browsers:
            if browser in paths:
                print(f"\n🌐 Prüfe {browser.title()}...")
                cookie_paths = paths[browser] if isinstance(paths[browser], list) else [paths[browser]]
                
                for cookie_path in cookie_paths:
                    if os.path.exists(cookie_path):
                        profile_name = os.path.basename(os.path.dirname(cookie_path))
                        print(f"  ✅ Gefunden: {profile_name}")
                        try:
                            browser_cookies = self.extract_chromium_cookies(cookie_path)
                            if browser_cookies:
                                self.cookies.update(browser_cookies)
                                print(f"  📊 {len(browser_cookies)} Cookies extrahiert")
                                return True  # Erfolgreich, stoppe bei erstem Fund
                        except Exception as e:
                            print(f"  ❌ Fehler: {e}")
                    else:
                        profile_name = os.path.basename(os.path.dirname(cookie_path))
                        print(f"  ❌ Profil nicht gefunden: {profile_name}")
        
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
        
        # Safari
        print(f"\n🍎 Prüfe Safari...")
        safari_path = paths['safari']
        if os.path.exists(safari_path):
            print(f"  ✅ Safari-Cookies gefunden")
            try:
                browser_cookies = self.extract_safari_cookies(safari_path)
                if browser_cookies:
                    self.cookies.update(browser_cookies)
                    print(f"  📊 {len(browser_cookies)} Cookies extrahiert")
                    return True
            except Exception as e:
                print(f"  ❌ Safari-Fehler: {e}")
        else:
            print(f"  ❌ Safari-Cookies nicht gefunden")
        
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
                output_file = os.path.join(os.path.expanduser("~"), "dl_cookies.json")
        
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
                'platform': 'macos',
                'cookie_details': self.cookies,
                'source': 'macos_extractor'
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
    print("🚀 macOS DL-Provider Cookie-Extraktor")
    print("=" * 43)
    print("🍎 Speziell optimiert für macOS-Systeme")
    print()
    
    # Warnung über geschlossene Browser
    print("⚠️  WICHTIG: Schließe alle Browser bevor du fortfährst!")
    print("📌 Dies verhindert Dateisperren bei der Cookie-Extraktion")
    input("\nDrücke Enter zum Fortfahren...")
    
    extractor = MacOSCookieExtractor()
    
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
        print("- macOS-Sicherheitseinstellungen blockieren Zugriff")
        
        print(f"\n💡 Tipp: Logge dich in deinem Browser bei {extractor.target_domain} ein und versuche es erneut")
        print("\n🔧 Debugging:")
        print("- Prüfe Browser-Installation: ls ~/Library/Application\\ Support/")
        print("- Prüfe Firefox-Profile: ls ~/Library/Application\\ Support/Firefox/Profiles/")
        print("- Prüfe Chrome-Profile: ls ~/Library/Application\\ Support/Google/Chrome/")
        print("\n🔒 Hinweis: macOS könnte zusätzliche Berechtigungen erfordern")

if __name__ == "__main__":
    main() 