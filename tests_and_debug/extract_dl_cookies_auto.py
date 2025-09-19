#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cookie-Extraktor für data-load.me (Automatisierte Version)
Extrahiert Cookies aus Browser-Datenbanken ohne User-Prompts
"""

import os
import json
import sqlite3
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
import sys

class BrowserCookieExtractor:
    """Extrahiert Cookies aus verschiedenen Browsern"""
    
    def __init__(self):
        self.target_domain = "data-load.me"
        self.cookies = {}
        
    def get_desktop_path(self):
        """Ermittelt den Desktop-Pfad des aktuellen Benutzers"""
        try:
            if os.name == 'nt':  # Windows
                desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
                if not os.path.exists(desktop_path):
                    # Fallback auf Benutzerverzeichnis
                    desktop_path = os.path.expanduser("~")
            elif sys.platform == 'darwin':  # macOS
                desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
                if not os.path.exists(desktop_path):
                    desktop_path = os.path.expanduser("~")
            else:  # Linux
                desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
                if not os.path.exists(desktop_path):
                    desktop_path = os.path.expanduser("~")
            
            return desktop_path
        except Exception as e:
            if not silent:
                print(f"⚠️ Warnung: Konnte Desktop-Pfad nicht ermitteln ({e}), verwende Arbeitsverzeichnis")
            return os.getcwd()
        
    def get_chrome_cookies(self):
        """Extrahiert Cookies aus Chrome"""
        try:
            # Chrome Cookie-Pfade für verschiedene OS
            if os.name == 'nt':  # Windows
                cookie_paths = [
                    os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data\Default\Network\Cookies"),
                    os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data\Profile 1\Network\Cookies"),
                ]
            elif sys.platform == 'darwin':  # macOS
                cookie_paths = [
                    os.path.expanduser("~/Library/Application Support/Google/Chrome/Default/Cookies"),
                ]
            else:  # Linux
                cookie_paths = [
                    os.path.expanduser("~/.config/google-chrome/Default/Cookies"),
                    os.path.expanduser("~/.config/chromium/Default/Cookies"),
                ]
            
            for cookie_path in cookie_paths:
                if os.path.exists(cookie_path):
                    print(f"[Chrome] Lese Cookies aus: {cookie_path}")
                    cookies = self._read_chrome_cookies(cookie_path)
                    if cookies:
                        self.cookies.update(cookies)
                        print(f"[Chrome] ✅ {len(cookies)} Cookies für {self.target_domain} gefunden")
                        return True
            
            print("[Chrome] ❌ Keine Chrome-Cookie-Datei gefunden")
            return False
            
        except Exception as e:
            print(f"[Chrome] ❌ Fehler: {e}")
            return False
    
    def _read_chrome_cookies(self, cookie_path):
        """Liest Chrome-Cookies aus SQLite-Datei"""
        cookies = {}
        
        # Temporäre Kopie erstellen (Chrome hat möglicherweise Datei gesperrt)
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as temp_file:
            temp_path = temp_file.name
        
        try:
            shutil.copy2(cookie_path, temp_path)
            
            conn = sqlite3.connect(temp_path)
            cursor = conn.cursor()
            
            # Chrome Cookie-Schema
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
            # Temporäre Datei löschen
            try:
                os.unlink(temp_path)
            except:
                pass
        
        return cookies
    
    def get_firefox_cookies(self):
        """Extrahiert Cookies aus Firefox"""
        try:
            if os.name == 'nt':  # Windows
                firefox_path = os.path.expandvars(r"%APPDATA%\Mozilla\Firefox\Profiles")
            elif sys.platform == 'darwin':  # macOS
                firefox_path = os.path.expanduser("~/Library/Application Support/Firefox/Profiles")
            else:  # Linux
                firefox_path = os.path.expanduser("~/.mozilla/firefox")
            
            if not os.path.exists(firefox_path):
                print("[Firefox] ❌ Firefox-Profil-Ordner nicht gefunden")
                return False
            
            # Suche nach Profil-Ordnern
            for profile_dir in os.listdir(firefox_path):
                profile_path = os.path.join(firefox_path, profile_dir)
                if os.path.isdir(profile_path):
                    cookies_db = os.path.join(profile_path, "cookies.sqlite")
                    if os.path.exists(cookies_db):
                        print(f"[Firefox] Lese Cookies aus: {cookies_db}")
                        cookies = self._read_firefox_cookies(cookies_db)
                        if cookies:
                            self.cookies.update(cookies)
                            print(f"[Firefox] ✅ {len(cookies)} Cookies für {self.target_domain} gefunden")
                            return True
            
            print("[Firefox] ❌ Keine Firefox-Cookie-Datei gefunden")
            return False
            
        except Exception as e:
            print(f"[Firefox] ❌ Fehler: {e}")
            return False
    
    def _read_firefox_cookies(self, cookie_path):
        """Liest Firefox-Cookies aus SQLite-Datei"""
        cookies = {}
        
        # Temporäre Kopie erstellen
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as temp_file:
            temp_path = temp_file.name
        
        try:
            shutil.copy2(cookie_path, temp_path)
            
            conn = sqlite3.connect(temp_path)
            cursor = conn.cursor()
            
            # Firefox Cookie-Schema
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
    
    def get_edge_cookies(self):
        """Extrahiert Cookies aus Microsoft Edge"""
        try:
            if os.name == 'nt':  # Windows
                cookie_paths = [
                    os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\User Data\Default\Network\Cookies"),
                ]
            elif sys.platform == 'darwin':  # macOS
                cookie_paths = [
                    os.path.expanduser("~/Library/Application Support/Microsoft Edge/Default/Cookies"),
                ]
            else:  # Linux
                cookie_paths = [
                    os.path.expanduser("~/.config/microsoft-edge/Default/Cookies"),
                ]
            
            for cookie_path in cookie_paths:
                if os.path.exists(cookie_path):
                    print(f"[Edge] Lese Cookies aus: {cookie_path}")
                    cookies = self._read_chrome_cookies(cookie_path)  # Edge verwendet Chrome-Format
                    if cookies:
                        self.cookies.update(cookies)
                        print(f"[Edge] ✅ {len(cookies)} Cookies für {self.target_domain} gefunden")
                        return True
            
            print("[Edge] ❌ Keine Edge-Cookie-Datei gefunden")
            return False
            
        except Exception as e:
            print(f"[Edge] ❌ Fehler: {e}")
            return False
    
    def extract_all_cookies(self, silent=False):
        """Extrahiert Cookies aus allen verfügbaren Browsern"""
        if not silent:
            print(f"Cookie-Extraktor für {self.target_domain}")
            print("=" * 50)
        
        success = False
        
        # Versuche alle Browser
        if self.get_chrome_cookies():
            success = True
        if self.get_firefox_cookies():
            success = True
        if self.get_edge_cookies():
            success = True
        
        return success
    
    def save_cookies_for_quasarr(self, output_file=None, silent=False):
        """Speichert Cookies im Quasarr-kompatiblen Format auf dem Desktop"""
        if not self.cookies:
            if not silent:
                print("❌ Keine Cookies gefunden!")
            return False
        
        # Wenn kein spezifischer Dateiname angegeben, speichere auf Desktop
        if output_file is None:
            desktop_path = self.get_desktop_path()
            output_file = os.path.join(desktop_path, "dl_cookies.json")
        
        # Konvertiere zu requests.Session kompatiblem Format
        session_cookies = {}
        for name, data in self.cookies.items():
            session_cookies[name] = data['value']
        
        # Erweiterte Metadaten für Debugging
        cookie_data = {
            'cookies': session_cookies,
            'metadata': {
                'domain': self.target_domain,
                'extracted_at': datetime.now().isoformat(),
                'total_cookies': len(session_cookies),
                'cookie_details': self.cookies
            }
        }
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(cookie_data, f, indent=2, ensure_ascii=False)
            
            if not silent:
                print(f"Cookies gespeichert auf Desktop: {output_file}")
                print(f"Insgesamt {len(session_cookies)} Cookies extrahiert")
                
                # Cookie-Übersicht anzeigen
                print("\nGefundene Cookies:")
                for name in session_cookies.keys():
                    print(f"  - {name}")
            
            return True
            
        except Exception as e:
            if not silent:
                print(f"❌ Fehler beim Speichern: {e}")
            return False

def extract_cookies_automated(output_file=None, silent=False):
    """Automatisierte Cookie-Extraktion ohne User-Prompts, Desktop-Speicherung"""
    extractor = BrowserCookieExtractor()
    
    if extractor.extract_all_cookies(silent=silent):
        if extractor.save_cookies_for_quasarr(output_file, silent=silent):
            if not silent:
                desktop_path = extractor.get_desktop_path()
                print(f"✅ Cookie-Datei wurde auf dem Desktop gespeichert: {os.path.join(desktop_path, 'dl_cookies.json')}")
            return True
        else:
            if not silent:
                print("❌ Fehler beim Speichern der Cookies")
            return False
    else:
        if not silent:
            print("❌ Keine Cookies gefunden! Stelle sicher, dass du bei data-load.me im Browser eingeloggt bist.")
        return False

def main():
    """Hauptfunktion für Stand-alone Verwendung"""
    import argparse
    
    parser = argparse.ArgumentParser(description="data-load.me Cookie-Extraktor")
    parser.add_argument("--output", "-o", default="dl_cookies.json", help="Output-Datei")
    parser.add_argument("--silent", "-s", action="store_true", help="Stille Ausführung")
    parser.add_argument("--auto", "-a", action="store_true", help="Automatisch ohne Prompts")
    
    args = parser.parse_args()
    
    if args.auto:
        success = extract_cookies_automated(args.output, args.silent)
        sys.exit(0 if success else 1)
    else:
        # Normale interaktive Version
        if not args.silent:
            print("🚀 data-load.me Cookie-Extraktor")
            print("Bitte stelle sicher, dass alle Browser geschlossen sind!")
            input("Drücke Enter zum Fortfahren...")
        
        success = extract_cookies_automated(args.output, args.silent)
        
        if success and not args.silent:
            print("\n✅ Erfolgreich! Die Cookie-Datei kann jetzt in Quasarr verwendet werden.")
            print("\n📋 Nächste Schritte:")
            print("1. Kopiere 'dl_cookies.json' ins Quasarr config-Verzeichnis")
            print("2. Setze die Umgebungsvariable: DL_COOKIES=/config/dl_cookies.json")
            print("3. Starte Quasarr neu")
        
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 