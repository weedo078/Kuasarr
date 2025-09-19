#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Test der echten Quasarr-Integration mit data-load.me

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

# Setze Umgebungsvariablen für Test
os.environ['DL_USER'] = 'weedo078'
os.environ['DL_PASSWORD'] = 'monEY125"'

def test_quasarr_dl_integration():
    """Teste die echte Quasarr data-load.me Integration"""
    
    print("=" * 60)
    print("QUASARR DATA-LOAD.ME INTEGRATION TEST")
    print("=" * 60)
    
    try:
        # Import der echten Quasarr-Module
        print("\n[1] Importiere Quasarr-Module...")
        
        from quasarr.search.sources import dl as search_dl
        from quasarr.downloads.sources import dl as download_dl
        
        print("    ✓ Module erfolgreich importiert")
        
        # Test Search-Funktionalität
        print("\n[2] Teste Search-Funktionalität...")
        
        search_query = "the last of us s02"
        print(f"    Suchbegriff: '{search_query}'")
        
        # Simuliere Quasarr Search-Call
        search_results = search_dl.search(search_query)
        
        print(f"    Suchergebnisse: {len(search_results) if search_results else 0}")
        
        if search_results and len(search_results) > 0:
            print("    ✓ Search funktioniert!")
            
            # Zeige erste 3 Ergebnisse
            for i, result in enumerate(search_results[:3], 1):
                print(f"      {i}. {result.get('title', 'Kein Titel')} - {result.get('size', 'Unbekannte Größe')}")
        else:
            print("    ✗ Keine Suchergebnisse")
            return False
        
        # Test Download-Funktionalität
        print("\n[3] Teste Download-Funktionalität...")
        
        test_url = "https://www.data-load.me/threads/the-last-of-us-s02-german-aac-1080p-web-x265-w00t.921932/"
        print(f"    Test-URL: {test_url}")
        
        # Simuliere Quasarr Download-Call
        download_links = download_dl.get_download_links(test_url)
        
        print(f"    Download-Links: {len(download_links) if download_links else 0}")
        
        if download_links and len(download_links) > 0:
            print("    ✓ Download-Extraktion funktioniert!")
            
            # Zeige erste 3 Download-Links
            for i, link in enumerate(download_links[:3], 1):
                print(f"      {i}. {link}")
        else:
            print("    ✗ Keine Download-Links extrahiert")
            return False
        
        # Test Feed-Funktionalität
        print("\n[4] Teste Feed-Funktionalität...")
        
        try:
            feed_results = search_dl.get_latest()
            print(f"    Feed-Ergebnisse: {len(feed_results) if feed_results else 0}")
            
            if feed_results and len(feed_results) > 0:
                print("    ✓ Feed funktioniert!")
                
                for i, result in enumerate(feed_results[:3], 1):
                    print(f"      {i}. {result.get('title', 'Kein Titel')}")
            else:
                print("    ⚠️ Feed leer oder nicht implementiert")
        except Exception as e:
            print(f"    ⚠️ Feed-Fehler: {e}")
        
        # Test Konfiguration
        print("\n[5] Teste Konfiguration...")
        
        # Prüfe ob Umgebungsvariablen gelesen werden
        if hasattr(download_dl, 'get_credentials'):
            try:
                creds = download_dl.get_credentials()
                if creds and creds.get('username'):
                    print("    ✓ Credentials aus Umgebungsvariablen gelesen")
                else:
                    print("    ⚠️ Credentials nicht gefunden")
            except:
                print("    ⚠️ Credential-Funktion nicht verfügbar")
        
        print(f"\n🎉 QUASARR-INTEGRATION ERFOLGREICH!")
        print(f"   ✓ Search funktioniert")
        print(f"   ✓ Download-Extraktion funktioniert")
        print(f"   ✓ Module sind korrekt integriert")
        
        return True
        
    except ImportError as e:
        print(f"\n❌ IMPORT-FEHLER: {e}")
        print("    Mögliche Ursachen:")
        print("    - Quasarr-Module nicht gefunden")
        print("    - Python-Path falsch")
        print("    - Abhängigkeiten fehlen")
        return False
        
    except Exception as e:
        print(f"\n❌ FEHLER: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_quasarr_dl_integration()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ QUASARR-INTEGRATION VOLLSTÄNDIG FUNKTIONSFÄHIG!")
    else:
        print("❌ QUASARR-INTEGRATION BENÖTIGT WEITERE ARBEIT")
    print("=" * 60) 