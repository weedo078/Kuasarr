#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import json
import os

def check_protected_packages():
    """Prüfe welche Pakete auf Captcha-Lösung warten"""
    
    db_path = "/config/Quasarr.db"
    if os.path.exists("config/Quasarr.db"):
        db_path = "config/Quasarr.db"
    
    if not os.path.exists(db_path):
        print(f"Datenbank nicht gefunden: {db_path}")
        return
    
    print("=== CAPTCHA-WARTENDE PAKETE ===\n")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Prüfe protected Tabelle
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='protected'")
        if not cursor.fetchone():
            print("Keine 'protected' Tabelle gefunden")
            return
        
        # Hole alle geschützten Pakete
        cursor.execute("SELECT * FROM protected")
        packages = cursor.fetchall()
        
        if not packages:
            print("Keine Pakete warten auf Captcha-Lösung")
        else:
            print(f"Gefunden: {len(packages)} Paket(e)\n")
            
            for i, (package_id, data) in enumerate(packages, 1):
                try:
                    package_data = json.loads(data)
                    print(f"Paket {i}:")
                    print(f"  ID: {package_id}")
                    print(f"  Titel: {package_data.get('title', 'N/A')}")
                    print(f"  Links: {package_data.get('links', [])}")
                    print(f"  Größe MB: {package_data.get('size_mb', 0)}")
                    print(f"  Passwort: {package_data.get('password', 'N/A')}")
                    print("-" * 80)
                except json.JSONDecodeError:
                    print(f"Paket {i}: Fehler beim Parsen der Daten")
                    print(f"  Raw data: {data}")
                    print("-" * 80)
        
        conn.close()
        
    except Exception as e:
        print(f"Fehler beim Zugriff auf Datenbank: {e}")
    
    print("\n=== FAILED PAKETE ===\n")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Prüfe failed Tabelle
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='failed'")
        if cursor.fetchone():
            cursor.execute("SELECT * FROM failed")
            failed_packages = cursor.fetchall()
            
            if failed_packages:
                print(f"Gefunden: {len(failed_packages)} fehlgeschlagene(s) Paket(e)\n")
                for i, (package_id, data) in enumerate(failed_packages, 1):
                    try:
                        package_data = json.loads(data)
                        if isinstance(package_data, str):
                            package_data = json.loads(package_data)
                        print(f"Failed Paket {i}:")
                        print(f"  ID: {package_id}")
                        print(f"  Titel: {package_data.get('title', 'N/A')}")
                        print(f"  Fehler: {package_data.get('error', 'N/A')}")
                        print("-" * 40)
                    except:
                        print(f"Failed Paket {i}: Parsing-Fehler")
            else:
                print("Keine fehlgeschlagenen Pakete")
        
        conn.close()
        
    except Exception as e:
        print(f"Fehler beim Lesen der failed-Tabelle: {e}")

if __name__ == "__main__":
    check_protected_packages() 