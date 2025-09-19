#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WSL-kompatible Cookie-Extraktor für data-load.me 
Kann Windows-Browser-Cookies aus WSL heraus lesen
"""

import os
import json
import sqlite3
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
import sys
import subprocess

class WSLBrowserCookieExtractor:
    """Extrahiert Cookies aus Windows-Browsern via WSL"""
    
    def __init__(self):
        self.target_domain = "data-load.me"
        self.cookies = {}
        
    def get_wsl_windows_path(self, windows_path):
        """Konvertiert Windows-Pfad zu WSL-Pfad"""
        # %LOCALAPPDATA% = C:\Users\username\AppData\Local
        # %APPDATA% = C:\Users\username\AppData\Roaming
        
        # Ermittle Windows-Username - bessere Methode für WSL
        username = None
        
        # Methode 1: Über WSLENV oder Windows-Umgebung
        try:
            # Versuche Windows-Username über USERPROFILE zu ermitteln
            result = subprocess.run(['wslpath', '-w', '~'], capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip():
                win_home = result.stdout.strip()
                # C:\Users\username -> username
                if "\\Users\\" in win_home:
                    username = win_home.split("\\Users\\")[1].split("\\")[0]
        except:
            pass
        
        # Methode 2: Über PowerShell USERPROFILE ermitteln
        if not username:
            try:
                result = subprocess.run(['powershell.exe', '-c', '$env:USERPROFILE'], 
                                      capture_output=True, text=True)
                if result.returncode == 0 and result.stdout.strip():
                    win_profile = result.stdout.strip()
                    if "\\Users\\" in win_profile:
                        username = win_profile.split("\\Users\\")[1].split("\\")[0]
            except:
                pass
        
        # Methode 3: Über /mnt/c/Users/ Verzeichnissen suchen
        if not username:
            try:
                users_dir = "/mnt/c/Users"
                if os.path.exists(users_dir):
                    # Suche nach dem Benutzer mit den meisten Browser-Daten
                    best_user = None
                    max_score = 0
                    
                    for user_folder in os.listdir(users_dir):
                        user_path = os.path.join(users_dir, user_folder)
                        if os.path.isdir(user_path) and user_folder not in ['Public', 'Default', 'All Users']:
                            # Score basierend auf Browser-Verzeichnissen
                            score = 0
                            
                            # Chrome
                            chrome_path = os.path.join(user_path, "AppData/Local/Google/Chrome")
                            if os.path.exists(chrome_path):
                                score += 2
                            
                            # Edge
                            edge_path = os.path.join(user_path, "AppData/Local/Microsoft/Edge")
                            if os.path.exists(edge_path):
                                score += 2
                            
                            # Firefox
                            firefox_path = os.path.join(user_path, "AppData/Roaming/Mozilla/Firefox")
                            if os.path.exists(firefox_path):
                                score += 2
                            
                            if score > max_score:
                                max_score = score
                                best_user = user_folder
                    
                    if best_user:
                        username = best_user
            except:
                pass
        
        # Fallback: aktueller WSL-User oder gianj
        if not username:
            username = os.environ.get("USER", "gianj")
        
        if not username:
            return None
        
        # Ersetze Windows-Umgebungsvariablen
        wsl_path = windows_path.replace("%LOCALAPPDATA%", f"/mnt/c/Users/{username}/AppData/Local")
        wsl_path = wsl_path.replace("%APPDATA%", f"/mnt/c/Users/{username}/AppData/Roaming")
        wsl_path = wsl_path.replace("\\", "/")
        
        return wsl_path
        
    def get_chrome_cookies(self):
        """Extrahiert Cookies aus Chrome (WSL-kompatibel)"""
        try:
            # Chrome Cookie-Pfade für WSL (Windows-Browser)
            windows_paths = [
                r"%LOCALAPPDATA%\Google\Chrome\User Data\Default\Network\Cookies",
                r"%LOCALAPPDATA%\Google\Chrome\User Data\Profile 1\Network\Cookies",
            ]
            
            cookie_paths = []
            for win_path in windows_paths:
                wsl_path = self.get_wsl_windows_path(win_path)
                if wsl_path:
                    cookie_paths.append(wsl_path)
            
            for cookie_path in cookie_paths:
                if os.path.exists(cookie_path):
                    print(f"[Chrome] Lese Cookies aus: {cookie_path}")
                    cookies = self._read_chrome_cookies(cookie_path)
                    if cookies:
                        self.cookies.update(cookies)
                        print(f"[Chrome] ✅ {len(cookies)} Cookies für {self.target_domain} gefunden")
                        return True
                else:
                    print(f"[Chrome] Pfad nicht gefunden: {cookie_path}")
            
            print("[Chrome] ❌ Keine Chrome-Cookie-Datei gefunden")
            return False
            
        except Exception as e:
            print(f"[Chrome] ❌ Fehler: {e}")
            return False
    
    def get_firefox_cookies(self):
        """Extrahiert Cookies aus Firefox (WSL-kompatibel)"""
        try:
            # Firefox-Pfad für WSL
            win_path = r"%APPDATA%\Mozilla\Firefox\Profiles"
            firefox_path = self.get_wsl_windows_path(win_path)
            
            if not firefox_path or not os.path.exists(firefox_path):
                print(f"[Firefox] ❌ Firefox-Profil-Ordner nicht gefunden: {firefox_path}")
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
    
    def get_edge_cookies(self):
        """Extrahiert Cookies aus Microsoft Edge (WSL-kompatibel)"""
        try:
            # Prüfe ob Edge läuft
            if not self.warn_about_running_browsers('edge'):
                return False
            
            # Edge Cookie-Pfade für WSL (Windows-Browser) - mehrere Profile
            windows_paths = [
                r"%LOCALAPPDATA%\Microsoft\Edge\User Data\Default\Network\Cookies",
                r"%LOCALAPPDATA%\Microsoft\Edge\User Data\Profile 1\Network\Cookies",
                r"%LOCALAPPDATA%\Microsoft\Edge\User Data\Profile 2\Network\Cookies",
                r"%LOCALAPPDATA%\Microsoft\Edge\User Data\Profile 3\Network\Cookies",
            ]
            
            cookie_paths = []
            for win_path in windows_paths:
                wsl_path = self.get_wsl_windows_path(win_path)
                if wsl_path:
                    cookie_paths.append(wsl_path)
            
            found_cookies = False
            for cookie_path in cookie_paths:
                if os.path.exists(cookie_path):
                    print(f"[Edge] Lese Cookies aus: {cookie_path}")
                    cookies = self._read_chrome_cookies(cookie_path)  # Edge verwendet Chrome-Format
                    if cookies:
                        self.cookies.update(cookies)
                        print(f"[Edge] ✅ {len(cookies)} Cookies für {self.target_domain} gefunden")
                        found_cookies = True
                else:
                    print(f"[Edge] Pfad nicht gefunden: {cookie_path}")
            
            if not found_cookies:
                print("[Edge] ❌ Keine Edge-Cookie-Datei gefunden oder nicht lesbar")
            
            return found_cookies
            
        except Exception as e:
            print(f"[Edge] ❌ Fehler: {e}")
            return False
    
    def _read_chrome_cookies(self, cookie_path):
        """Liest Chrome-Cookies aus SQLite-Datei"""
        cookies = {}
        
        # Prüfe ob Datei existiert und lesbar ist
        if not os.path.exists(cookie_path):
            print(f"    ❌ Datei existiert nicht: {cookie_path}")
            return cookies
        
        # Temporäre Kopie erstellen (Browser hat möglicherweise Datei gesperrt)
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as temp_file:
            temp_path = temp_file.name
        
        try:
            # Verschiedene Methoden um die gesperrte Datei zu kopieren
            copy_success = False
            
            # Methode 1: Normale Kopie
            try:
                shutil.copy2(cookie_path, temp_path)
                copy_success = True
                print(f"    ✅ Cookie-Datei erfolgreich kopiert")
            except PermissionError:
                print(f"    ⚠️  Permission denied - Browser läuft wahrscheinlich noch")
                
                # Methode 2: PowerShell robocopy (Windows)
                try:
                    # Konvertiere WSL-Pfade zu Windows-Pfaden für robocopy
                    win_source = cookie_path.replace('/mnt/c/', 'C:\\').replace('/', '\\')
                    win_temp = temp_path.replace('/mnt/c/', 'C:\\').replace('/', '\\')
                    
                    import subprocess
                    # Robocopy mit /B (backup mode) um gesperrte Dateien zu kopieren
                    result = subprocess.run([
                        'powershell.exe', '-c', 
                        f'robocopy (Split-Path "{win_source}") (Split-Path "{win_temp}") (Split-Path -Leaf "{win_source}") /B /NP /NDL /NJH /NJS'
                    ], capture_output=True, text=True)
                    
                    # Umbenenne die kopierte Datei
                    copied_file = os.path.join(os.path.dirname(temp_path), os.path.basename(cookie_path))
                    if os.path.exists(copied_file):
                        os.rename(copied_file, temp_path)
                        copy_success = True
                        print(f"    ✅ Cookie-Datei mit robocopy kopiert")
                    
                except Exception as e:
                    print(f"    ❌ Robocopy fehlgeschlagen: {e}")
                
                # Methode 3: Volume Shadow Copy (VSS) - für locked files
                if not copy_success:
                    try:
                        # Erstelle Shadow Copy und kopiere von dort
                        vss_result = subprocess.run([
                            'powershell.exe', '-c', 
                            f'''
                            $shadow = (Get-WmiObject -Class Win32_ShadowCopy | Sort-Object InstallDate -Descending | Select-Object -First 1)
                            if ($shadow) {{
                                $shadowPath = $shadow.DeviceObject + "\\Users\\gianj\\AppData\\Local\\Microsoft\\Edge\\User Data\\Default\\Network\\Cookies"
                                if (Test-Path $shadowPath) {{
                                    Copy-Item $shadowPath "{win_temp}" -Force
                                    Write-Output "SUCCESS"
                                }}
                            }}
                            '''
                        ], capture_output=True, text=True)
                        
                        if "SUCCESS" in vss_result.stdout:
                            copy_success = True
                            print(f"    ✅ Cookie-Datei von Shadow Copy kopiert")
                        
                    except Exception as e:
                        print(f"    ❌ Shadow Copy fehlgeschlagen: {e}")
            
            except Exception as e:
                print(f"    ❌ Fehler beim Kopieren: {e}")
            
            if not copy_success:
                print(f"    ❌ Konnte Cookie-Datei nicht kopieren. Ist {os.path.basename(os.path.dirname(os.path.dirname(cookie_path)))} geschlossen?")
                return cookies
            
            # SQLite-Datei lesen
            try:
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
                print(f"    ✅ {len(cookies)} Cookies für {self.target_domain} gefunden")
                
            except Exception as e:
                print(f"    ❌ Fehler beim Lesen der SQLite-Datei: {e}")
            
        finally:
            # Temporäre Datei löschen
            try:
                os.unlink(temp_path)
            except:
                pass
        
        return cookies
    
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
    
    def extract_all_cookies(self, silent=False):
        """Extrahiert Cookies aus allen verfügbaren Browsern"""
        if not silent:
            print(f"WSL Cookie-Extraktor für {self.target_domain}")
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
    
    def get_desktop_path(self, silent=False):
        """Ermittelt den Desktop-Pfad in WSL-Umgebung"""
        try:
            # WSL: Versuche den Windows-Desktop über /mnt/c zu erreichen
            username = self._get_username()
            if username:
                # Windows Desktop-Pfad
                win_desktop = f"/mnt/c/Users/{username}/Desktop"
                if os.path.exists(win_desktop):
                    return win_desktop
                
                # Fallback auf Windows-Benutzerverzeichnis
                win_user = f"/mnt/c/Users/{username}"
                if os.path.exists(win_user):
                    return win_user
            
            # Linux-Desktop innerhalb WSL
            linux_desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            if os.path.exists(linux_desktop):
                return linux_desktop
            
            # Letzter Fallback
            return os.path.expanduser("~")
            
        except Exception as e:
            if not silent:
                print(f"⚠️ Warnung: Konnte Desktop-Pfad nicht ermitteln ({e}), verwende Home-Verzeichnis")
            return os.path.expanduser("~")
    
    def save_cookies_for_quasarr(self, output_file=None, silent=False):
        """Speichert Cookies im Quasarr-kompatiblen Format im aktuellen Verzeichnis"""
        if not self.cookies:
            if not silent:
                print("❌ Keine Cookies gefunden!")
            return False
        
        # Wenn kein spezifischer Dateiname angegeben, speichere im aktuellen Verzeichnis
        if output_file is None:
            current_dir = os.getcwd()
            output_file = os.path.join(current_dir, "dl_cookies.json")
        
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
                'cookie_details': self.cookies,
                'source': 'wsl_extractor'
            }
        }
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(cookie_data, f, indent=2, ensure_ascii=False)
            
            if not silent:
                print(f"✅ Cookies gespeichert in: {output_file}")
                print(f"📊 Insgesamt {len(session_cookies)} Cookies extrahiert")
                
                # Cookie-Übersicht anzeigen
                print("\n🔍 Gefundene Cookies:")
                for name in session_cookies.keys():
                    print(f"  - {name}")
            
            return True
            
        except Exception as e:
            if not silent:
                print(f"❌ Fehler beim Speichern: {e}")
            return False
    
    def check_available_browsers(self):
        """Überprüft welche Browser verfügbar sind"""
        available = {}
        
        # Username ermitteln
        username = self._get_username()
        if not username:
            return available
        
        base_local = f"/mnt/c/Users/{username}/AppData/Local"
        base_roaming = f"/mnt/c/Users/{username}/AppData/Roaming"
        
        # Chrome prüfen
        chrome_paths = [
            f"{base_local}/Google/Chrome/User Data/Default/Network/Cookies",
            f"{base_local}/Google/Chrome/User Data/Profile 1/Network/Cookies",
        ]
        chrome_found = any(os.path.exists(path) for path in chrome_paths)
        if chrome_found:
            available['chrome'] = 'Google Chrome'
        
        # Edge prüfen
        edge_paths = [
            f"{base_local}/Microsoft/Edge/User Data/Default/Network/Cookies",
            f"{base_local}/Microsoft/Edge/User Data/Profile 1/Network/Cookies",
        ]
        edge_found = any(os.path.exists(path) for path in edge_paths)
        if edge_found:
            available['edge'] = 'Microsoft Edge'
        
        # Firefox prüfen
        firefox_base = f"{base_roaming}/Mozilla/Firefox/Profiles"
        firefox_found = False
        if os.path.exists(firefox_base):
            try:
                for profile in os.listdir(firefox_base):
                    profile_path = os.path.join(firefox_base, profile)
                    if os.path.isdir(profile_path):
                        cookies_path = os.path.join(profile_path, "cookies.sqlite")
                        if os.path.exists(cookies_path):
                            firefox_found = True
                            break
            except:
                pass
        if firefox_found:
            available['firefox'] = 'Mozilla Firefox'
        
        return available
    
    def _get_username(self):
        """Hilfsfunktion um Username zu ermitteln (extrahiert aus get_wsl_windows_path)"""
        username = None
        
        # Methode 1: PowerShell USERPROFILE
        try:
            import subprocess
            result = subprocess.run(['powershell.exe', '-c', '$env:USERPROFILE'], 
                                  capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip():
                win_profile = result.stdout.strip()
                if "\\Users\\" in win_profile:
                    username = win_profile.split("\\Users\\")[1].split("\\")[0]
        except:
            pass
        
        # Fallback
        if not username:
            username = os.environ.get("USER", "gianj")
        
        return username
    
    def extract_specific_browser(self, browser_choice, silent=False):
        """Extrahiert Cookies nur vom gewählten Browser"""
        if not silent:
            browser_names = {
                'chrome': 'Google Chrome',
                'edge': 'Microsoft Edge', 
                'firefox': 'Mozilla Firefox'
            }
            print(f"Extrahiere Cookies von {browser_names.get(browser_choice, browser_choice)}...")
        
        success = False
        
        if browser_choice == 'chrome':
            success = self.get_chrome_cookies()
        elif browser_choice == 'edge':
            success = self.get_edge_cookies()
        elif browser_choice == 'firefox':
            success = self.get_firefox_cookies()
        else:
            if not silent:
                print(f"❌ Unbekannter Browser: {browser_choice}")
            return False
        
        return success
    
    def check_running_browsers(self):
        """Prüft welche Browser-Prozesse laufen"""
        try:
            import subprocess
            result = subprocess.run([
                'powershell.exe', '-c', 
                'Get-Process | Where-Object {$_.ProcessName -match "chrome|msedge|firefox"} | Select-Object ProcessName, Id'
            ], capture_output=True, text=True)
            
            if result.returncode == 0 and result.stdout.strip():
                lines = result.stdout.strip().split('\n')
                processes = []
                for line in lines[2:]:  # Skip header lines
                    if line.strip():
                        parts = line.strip().split()
                        if len(parts) >= 2:
                            process_name = parts[0]
                            if process_name.lower() in ['chrome', 'msedge', 'firefox']:
                                processes.append(process_name)
                
                return list(set(processes))  # Remove duplicates
        except:
            pass
        
        return []
    
    def warn_about_running_browsers(self, target_browser=None):
        """Warnt vor laufenden Browser-Prozessen"""
        running = self.check_running_browsers()
        
        if not running:
            return True  # Keine laufenden Browser
        
        print(f"\n⚠️  Folgende Browser-Prozesse laufen noch:")
        for process in running:
            browser_name = {
                'chrome': 'Google Chrome',
                'msedge': 'Microsoft Edge', 
                'firefox': 'Mozilla Firefox'
            }.get(process.lower(), process)
            print(f"   - {browser_name} ({process})")
        
        if target_browser:
            target_process = {
                'chrome': 'chrome',
                'edge': 'msedge',
                'firefox': 'firefox'
            }.get(target_browser.lower(), target_browser)
            
            if target_process in [p.lower() for p in running]:
                print(f"\n❌ {target_browser.title()} läuft noch! Cookie-Datei ist wahrscheinlich gesperrt.")
                print(f"💡 Bitte schließe {target_browser.title()} komplett und versuche es erneut.")
                return False
        
        print(f"\n💡 Für beste Ergebnisse sollten alle Browser geschlossen werden.")
        return True

def extract_cookies_wsl(output_file=None, silent=False, browser_choice=None):
    """WSL Cookie-Extraktion mit Desktop-Speicherung"""
    extractor = WSLBrowserCookieExtractor()
    
    if not silent:
        print("WSL Cookie-Extraktor für data-load.me")
        print("=" * 50)
    
    # Browser auswählen, wenn nicht angegeben
    if not browser_choice:
        available = extractor.check_available_browsers()
        if not available:
            if not silent:
                print("❌ Keine Browser mit data-load.me Cookies gefunden!")
                print("\n💡 Tipps:")
                print("- Logge dich bei data-load.me im Windows-Browser ein")
                print("- Stelle sicher, dass der Browser geschlossen ist")
            return False
        
        if not silent:
            print("Verfügbare Browser:")
            choices = list(available.keys())
            for i, (key, name) in enumerate(available.items(), 1):
                print(f"{i}. {name}")
            
            while True:
                try:
                    choice = input(f"Wähle Browser (1-{len(choices)}): ")
                    idx = int(choice) - 1
                    if 0 <= idx < len(choices):
                        browser_choice = choices[idx]
                        break
                    else:
                        print("Ungültige Auswahl!")
                except (ValueError, KeyboardInterrupt):
                    print("Abgebrochen.")
                    return False
        else:
            # Silent mode: nimm ersten verfügbaren Browser
            browser_choice = list(available.keys())[0]
    
    # Cookies vom gewählten Browser extrahieren
    if extractor.extract_specific_browser(browser_choice, silent=silent):
        if extractor.save_cookies_for_quasarr(output_file, silent=silent):
            if not silent:
                desktop_path = extractor.get_desktop_path(silent)
                print(f"\n✅ Cookie-Datei wurde auf dem Desktop gespeichert!")
                print(f"📍 Speicherort: {os.path.join(desktop_path, 'dl_cookies.json')}")
            return True
        else:
            if not silent:
                print("❌ Fehler beim Speichern der Cookies")
            return False
    else:
        if not silent:
            print(f"❌ Keine Cookies in {browser_choice} gefunden!")
            print("\n💡 Debug-Informationen:")
            print("- Bist du bei data-load.me im Browser eingeloggt?")
            print("- Ist der Browser geschlossen?")
            print("- Läuft das Script in WSL?")
        return False

def main():
    """Hauptfunktion"""
    import argparse
    
    parser = argparse.ArgumentParser(description="data-load.me Cookie-Extraktor für WSL")
    parser.add_argument("--output", "-o", default="dl_cookies.json", help="Output-Datei")
    parser.add_argument("--silent", "-s", action="store_true", help="Stille Ausführung")
    parser.add_argument("--auto", "-a", action="store_true", help="Automatisch ohne Prompts")
    parser.add_argument("--browser", "-b", choices=['chrome', 'edge', 'firefox'], 
                       help="Browser auswählen (chrome/edge/firefox)")
    
    args = parser.parse_args()
    
    if args.auto:
        success = extract_cookies_wsl(args.output, args.silent, args.browser)
        sys.exit(0 if success else 1)
    else:
        # Normale interaktive Version
        if not args.silent:
            print("🚀 WSL data-load.me Cookie-Extraktor")
            print("Bitte stelle sicher, dass alle Browser geschlossen sind!")
            
            if not args.browser:
                input("Drücke Enter zum Fortfahren...")
        
        success = extract_cookies_wsl(args.output, args.silent, args.browser)
        
        if success and not args.silent:
            print("\n✅ Erfolgreich! Die Cookie-Datei kann jetzt in Quasarr verwendet werden.")
        
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 