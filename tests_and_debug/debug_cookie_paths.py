#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Debug-Skript für Cookie-Pfade in WSL
"""

import os
import subprocess

def get_wsl_windows_username():
    """Ermittelt Windows-Username in WSL"""
    print("🔍 Ermittle Windows-Username...")
    
    username = None
    methods = []
    
    # Methode 1: wslpath
    try:
        result = subprocess.run(['wslpath', '-w', '~'], capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            win_home = result.stdout.strip()
            methods.append(f"wslpath: {win_home}")
            if "\\Users\\" in win_home:
                username = win_home.split("\\Users\\")[1].split("\\")[0]
                methods.append(f"  -> Username: {username}")
    except Exception as e:
        methods.append(f"wslpath fehlgeschlagen: {e}")
    
    # Methode 2: PowerShell
    if not username:
        try:
            result = subprocess.run(['powershell.exe', '-c', '$env:USERPROFILE'], 
                                  capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip():
                win_profile = result.stdout.strip()
                methods.append(f"PowerShell USERPROFILE: {win_profile}")
                if "\\Users\\" in win_profile:
                    username = win_profile.split("\\Users\\")[1].split("\\")[0]
                    methods.append(f"  -> Username: {username}")
        except Exception as e:
            methods.append(f"PowerShell fehlgeschlagen: {e}")
    
    # Methode 3: /mnt/c/Users durchsuchen
    if not username:
        try:
            users_dir = "/mnt/c/Users"
            methods.append(f"Users-Verzeichnis: {users_dir}")
            if os.path.exists(users_dir):
                users = os.listdir(users_dir)
                methods.append(f"Gefundene Users: {users}")
                
                # Score alle User
                user_scores = {}
                for user_folder in users:
                    if user_folder in ['Public', 'Default', 'All Users']:
                        continue
                    
                    user_path = os.path.join(users_dir, user_folder)
                    if not os.path.isdir(user_path):
                        continue
                    
                    score = 0
                    browser_info = []
                    
                    # Chrome
                    chrome_path = os.path.join(user_path, "AppData/Local/Google/Chrome")
                    if os.path.exists(chrome_path):
                        score += 2
                        browser_info.append("Chrome")
                    
                    # Edge
                    edge_path = os.path.join(user_path, "AppData/Local/Microsoft/Edge")
                    if os.path.exists(edge_path):
                        score += 2
                        browser_info.append("Edge")
                    
                    # Firefox
                    firefox_path = os.path.join(user_path, "AppData/Roaming/Mozilla/Firefox")
                    if os.path.exists(firefox_path):
                        score += 2
                        browser_info.append("Firefox")
                    
                    user_scores[user_folder] = {
                        'score': score,
                        'browsers': browser_info
                    }
                    methods.append(f"  {user_folder}: Score={score}, Browser={browser_info}")
                
                if user_scores:
                    best_user = max(user_scores.keys(), key=lambda u: user_scores[u]['score'])
                    username = best_user
                    methods.append(f"  -> Bester User: {username}")
            else:
                methods.append(f"Users-Verzeichnis existiert nicht")
        except Exception as e:
            methods.append(f"Users-Suche fehlgeschlagen: {e}")
    
    # Fallback
    if not username:
        username = os.environ.get("USER", "gianj")
        methods.append(f"Fallback Username: {username}")
    
    for method in methods:
        print(f"  {method}")
    
    return username

def check_browser_paths(username):
    """Überprüft Browser-Cookie-Pfade"""
    print(f"\n🔍 Überprüfe Browser-Pfade für User: {username}")
    print("=" * 60)
    
    base_local = f"/mnt/c/Users/{username}/AppData/Local"
    base_roaming = f"/mnt/c/Users/{username}/AppData/Roaming"
    
    # Chrome-Pfade
    print("\n📱 Chrome:")
    chrome_paths = [
        f"{base_local}/Google/Chrome/User Data/Default/Network/Cookies",
        f"{base_local}/Google/Chrome/User Data/Profile 1/Network/Cookies",
        f"{base_local}/Google/Chrome/User Data/Profile 2/Network/Cookies",
    ]
    
    for path in chrome_paths:
        exists = "✅" if os.path.exists(path) else "❌"
        print(f"  {exists} {path}")
    
    # Edge-Pfade
    print("\n🌐 Edge:")
    edge_paths = [
        f"{base_local}/Microsoft/Edge/User Data/Default/Network/Cookies",
        f"{base_local}/Microsoft/Edge/User Data/Profile 1/Network/Cookies",
        f"{base_local}/Microsoft/Edge/User Data/Profile 2/Network/Cookies",
    ]
    
    for path in edge_paths:
        exists = "✅" if os.path.exists(path) else "❌"
        print(f"  {exists} {path}")
    
    # Firefox-Pfade
    print("\n🦊 Firefox:")
    firefox_base = f"{base_roaming}/Mozilla/Firefox/Profiles"
    if os.path.exists(firefox_base):
        print(f"  ✅ {firefox_base}")
        try:
            for profile in os.listdir(firefox_base):
                profile_path = os.path.join(firefox_base, profile)
                if os.path.isdir(profile_path):
                    cookies_path = os.path.join(profile_path, "cookies.sqlite")
                    exists = "✅" if os.path.exists(cookies_path) else "❌"
                    print(f"    {exists} {cookies_path}")
        except Exception as e:
            print(f"    ❌ Fehler beim Lesen der Profile: {e}")
    else:
        print(f"  ❌ {firefox_base}")

def main():
    print("🚀 WSL Cookie-Pfad Debug Tool")
    print("=" * 60)
    
    username = get_wsl_windows_username()
    check_browser_paths(username)
    
    print(f"\n✅ Debug abgeschlossen. Erkannter Username: {username}")

if __name__ == "__main__":
    main() 