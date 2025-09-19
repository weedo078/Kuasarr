#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test-Skript für die verbesserte Cookie-Extraktion
"""

import os
import sys

# Füge das Skript zum Python-Pfad hinzu
sys.path.insert(0, '.')

try:
    from extract_dl_cookies_wsl import WSLBrowserCookieExtractor
    
    def test_browser_detection():
        """Testet die Browser-Erkennung"""
        print("🔍 Teste Browser-Erkennung...")
        
        extractor = WSLBrowserCookieExtractor()
        available = extractor.check_available_browsers()
        
        print(f"✅ Verfügbare Browser: {len(available)}")
        for key, name in available.items():
            print(f"  - {key}: {name}")
        
        return available
    
    def test_interactive_mode():
        """Zeigt wie der interaktive Modus funktioniert"""
        print("\n🎯 Interaktiver Modus (Simulation):")
        print("Das Script würde dich fragen:")
        
        extractor = WSLBrowserCookieExtractor()
        available = extractor.check_available_browsers()
        
        if available:
            print("\n🌐 Verfügbare Browser mit Cookies:")
            for key, name in available.items():
                print(f"  [{key}] {name}")
            
            print(f"\nWähle einen Browser ({'/'.join(available.keys())}): ")
            print("(Du würdest hier einen eingeben, z.B. 'edge')")
        else:
            print("❌ Keine Browser gefunden")
    
    def main():
        print("🚀 Cookie-Extraktor Test")
        print("=" * 50)
        
        # Browser-Erkennung testen
        available = test_browser_detection()
        
        # Interaktiven Modus zeigen
        test_interactive_mode()
        
        print("\n📋 Verwendung:")
        print("# Interaktiv (wähle Browser):")
        print("wsl python3 extract_dl_cookies_wsl.py")
        print("")
        print("# Spezifischen Browser direkt:")
        print("wsl python3 extract_dl_cookies_wsl.py --browser edge")
        print("")
        print("# Auto-Modus (nimmt ersten verfügbaren):")
        print("wsl python3 extract_dl_cookies_wsl.py --auto")
        print("")
        print("# Auto-Modus mit spezifischem Browser:")
        print("wsl python3 extract_dl_cookies_wsl.py --auto --browser edge")
        
        if available:
            print(f"\n💡 Empfehlung: Verwende --browser {list(available.keys())[0]} für deinen bevorzugten Browser")
    
    if __name__ == "__main__":
        main()

except ImportError as e:
    print(f"❌ Fehler beim Importieren: {e}")
    print("Stelle sicher, dass extract_dl_cookies_wsl.py im gleichen Verzeichnis ist.") 