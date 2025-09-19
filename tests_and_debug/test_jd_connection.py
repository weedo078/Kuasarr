#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import hashlib
import hmac
import time
import base64

class MyJDApi:
    """Vereinfachte My JDownloader API für Tests"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session_token = None
        self.login_secret = None
        self.device_secret = None
        self.request_id = int(time.time() * 1000)
        self.api_url = "http://api.jdownloader.org"
        
    def test_connection(self, email, password):
        """Testet die Verbindung zu My JDownloader"""
        
        print("=== MY JDOWNLOADER CONNECTION TEST ===")
        print(f"Email: {email}")
        print(f"Password: {'*' * len(password)}")
        print()
        
        try:
            # 1. Connect
            print("1. Teste API-Verbindung...")
            connect_response = self.session.post(f"{self.api_url}/my/connect", 
                                               data={"email": email, "password": password})
            
            if connect_response.status_code != 200:
                print(f"❌ Connect fehlgeschlagen: {connect_response.status_code}")
                print(f"Response: {connect_response.text}")
                return False
                
            connect_data = connect_response.json()
            print(f"✅ Connect erfolgreich: {connect_data}")
            
            self.session_token = connect_data.get("sessiontoken")
            self.login_secret = connect_data.get("loginsecret")
            
            if not self.session_token or not self.login_secret:
                print("❌ Fehlende Session-Daten!")
                return False
            
            # 2. List Devices
            print("\n2. Lade verfügbare Geräte...")
            devices_response = self.session.post(f"{self.api_url}/my/listdevices", 
                                               data={"sessiontoken": self.session_token})
            
            if devices_response.status_code != 200:
                print(f"❌ Device-Liste fehlgeschlagen: {devices_response.status_code}")
                return False
                
            devices_data = devices_response.json()
            devices = devices_data.get("list", [])
            
            print(f"✅ Gefundene Geräte: {len(devices)}")
            
            if not devices:
                print("❌ PROBLEM: Keine Geräte gefunden!")
                print("   Lösung: Installiere JDownloader und logge dich ein, oder")
                print("   starte JDownloader und verbinde es mit My JDownloader")
                return False
            
            for i, device in enumerate(devices):
                name = device.get("name", "Unbekannt")
                device_type = device.get("type", "Unbekannt") 
                status = device.get("status", "Unbekannt")
                print(f"   Device {i+1}: '{name}' (Typ: {device_type}, Status: {status})")
                
                # Teste Verbindung zu diesem Device
                device_id = device.get("id")
                if device_id and status == "ONLINE":
                    print(f"      → Teste Verbindung zu '{name}'...")
                    try:
                        # Einfacher Ping-Test
                        ping_data = {
                            "sessiontoken": self.session_token,
                            "action": "/device/ping"
                        }
                        ping_response = self.session.post(f"{self.api_url}/my/listdevices", 
                                                        data=ping_data)
                        if ping_response.status_code == 200:
                            print(f"      ✅ '{name}' ist erreichbar!")
                        else:
                            print(f"      ⚠️ '{name}' antwortet nicht")
                    except:
                        print(f"      ⚠️ Fehler beim Testen von '{name}'")
            
            print("\n3. Test-Zusammenfassung:")
            online_devices = [d for d in devices if d.get("status") == "ONLINE"]
            
            if online_devices:
                print(f"✅ {len(online_devices)} Online-Gerät(e) gefunden!")
                print("   Deine JDownloader-Zugangsdaten sind KORREKT!")
                print("   Verwende einen dieser Device-Namen in Quasarr:")
                for device in online_devices:
                    print(f"     - '{device.get('name')}'")
                return True
            else:
                print("⚠️ Keine Online-Geräte gefunden!")
                print("   Deine Zugangsdaten sind korrekt, aber:")
                print("   - Stelle sicher, dass JDownloader läuft")
                print("   - Prüfe die Internet-Verbindung von JDownloader")
                print("   - Logge dich in JDownloader in My JDownloader ein")
                return False
                
        except Exception as e:
            print(f"❌ FEHLER: {e}")
            import traceback
            traceback.print_exc()
            return False

def main():
    """Hauptfunktion für den Test"""
    
    print("My JDownloader Verbindungstest")
    print("==============================")
    
    # Bitte User um Eingabe
    email = input("Deine My JDownloader E-Mail: ").strip()
    password = input("Dein My JDownloader Passwort: ").strip()
    
    if not email or not password:
        print("❌ E-Mail und Passwort sind erforderlich!")
        return
    
    api = MyJDApi()
    success = api.test_connection(email, password)
    
    if success:
        print("\n🎉 MY JDOWNLOADER VERBINDUNG ERFOLGREICH! 🎉")
        print("Du kannst diese Zugangsdaten in Quasarr verwenden!")
    else:
        print("\n❌ MY JDOWNLOADER VERBINDUNG FEHLGESCHLAGEN! ❌")
        print("Prüfe deine Zugangsdaten und JDownloader-Installation!")

if __name__ == "__main__":
    main() 