#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Finaler Test der data-load.me API-Integration

import requests
import json
import sys

def test_quasarr_api():
    """Testet die Quasarr API mit data-load.me Integration"""
    
    print("=== QUASARR DATA-LOAD.ME API TEST ===")
    
    # API-Details aus den Logs
    api_key = "cf2eb62ff6d9651d3e0d43d3b79b6a9e106de8808aa62403f6385c8dca913fab"  # Aus den Container-Logs
    base_url = "http://192.168.178.76:8080"
    
    print(f"API-URL: {base_url}")
    print(f"API-Key: {api_key[:10]}...")
    
    # Test 1: Capabilities (prüft ob API läuft)
    print("\n[1] Teste API Capabilities...")
    try:
        caps_url = f"{base_url}/api/v1/indexer/{api_key}/caps"
        response = requests.get(caps_url, timeout=10)
        print(f"    Status: {response.status_code}")
        
        if response.status_code == 200:
            print("    ✅ API ist erreichbar")
            # Zeige verfügbare Kategorien
            if 'xml' in response.headers.get('content-type', ''):
                print("    XML-Response erhalten")
            else:
                print(f"    Content: {response.text[:200]}")
        else:
            print(f"    ❌ API-Fehler: {response.text}")
            return False
    except Exception as e:
        print(f"    ❌ Verbindungsfehler: {e}")
        return False
    
    # Test 2: Konfigurations-Status (prüft ob Hostnames gesetzt sind)
    print("\n[2] Teste Status (ohne Hostname-Konfiguration)...")
    try:
        search_url = f"{base_url}/api/v1/indexer/{api_key}/search"
        params = {
            't': 'search',
            'q': 'test',
            'cat': '5000'  # TV
        }
        
        response = requests.get(search_url, params=params, timeout=15)
        print(f"    Status: {response.status_code}")
        print(f"    Content: {response.text[:300]}")
        
        # Suche nach "Starting X search functions"
        if "Starting 0 search functions" in response.text:
            print("    ❌ Immer noch 0 Suchfunktionen!")
            print("    → data-load.me muss noch konfiguriert werden")
        elif "search functions" in response.text:
            import re
            match = re.search(r'Starting (\d+) search functions', response.text)
            if match:
                num_functions = match.group(1)
                print(f"    ✅ {num_functions} Suchfunktionen verfügbar!")
                if int(num_functions) > 0:
                    print("    🎉 data-load.me Integration ERFOLGREICH!")
                    return True
        
        return False
        
    except Exception as e:
        print(f"    ❌ Such-Fehler: {e}")
        return False

def test_manual_configuration():
    """Anleitung für manuelle Konfiguration"""
    print("\n=== MANUELLE KONFIGURATION ERFORDERLICH ===")
    print("1. Öffne: http://192.168.178.76:8080")
    print("2. Gehe zu Hostnames-Konfiguration")
    print("3. Setze DL-Hostname: data-load.me")
    print("4. Setze JDownloader-Credentials:")
    print("   Email: te.ch.no.id.ac@gmail.com")
    print("   Password: monEY125$Gianni1998")
    print("5. Starte Quasarr neu")
    print("6. Führe diesen Test erneut aus")

if __name__ == "__main__":
    success = test_quasarr_api()
    
    if not success:
        test_manual_configuration()
        print("\n❌ Test fehlgeschlagen - Konfiguration erforderlich")
        sys.exit(1)
    else:
        print("\n🎉 INTEGRATION ERFOLGREICH!")
        sys.exit(0) 