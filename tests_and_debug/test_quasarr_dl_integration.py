#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import xml.etree.ElementTree as ET
from urllib.parse import urlencode
import json

def test_quasarr_dl_debug(base_url, api_key):
    """Detaillierter Test der data-load.me Integration in Quasarr"""
    
    print("=== QUASARR DATA-LOAD.ME DEBUG TEST ===")
    print(f"Base URL: {base_url}")
    print()
    
    try:
        # 1. Test verschiedene Suchbegriffe die auf data-load.me existieren sollten
        test_queries = [
            "American Horror Story",
            "The Walking Dead", 
            "Matrix",
            "Game of Thrones",
            "Breaking Bad",
            "Stranger Things"
        ]
        
        print("1. Teste bekannte Serien/Filme...")
        total_results = 0
        
        for query in test_queries:
            print(f"\n   Suche: '{query}'")
            
            # Test mit allen Kategorien
            params = {
                't': 'search',
                'apikey': api_key,
                'q': query
            }
            
            search_url = f"{base_url}/api?" + urlencode(params)
            
            try:
                response = requests.get(search_url, timeout=20)
                print(f"   Status: {response.status_code}")
                
                if response.status_code == 200:
                    try:
                        root = ET.fromstring(response.text)
                        items = root.findall(".//item")
                        result_count = len(items)
                        total_results += result_count
                        
                        if result_count > 0:
                            print(f"   ✅ {result_count} Ergebnisse gefunden!")
                            
                            # Zeige erste 2 Ergebnisse
                            for i, item in enumerate(items[:2]):
                                title = item.find("title")
                                title_text = title.text if title is not None else "N/A"
                                
                                link = item.find("link")
                                link_text = link.text if link is not None else "N/A"
                                
                                print(f"     {i+1}. {title_text}")
                                if "data-load.me" in link_text:
                                    print(f"        ✅ data-load.me Link gefunden!")
                                else:
                                    print(f"        ⚠️ Kein data-load.me Link: {link_text}")
                        else:
                            print(f"   ❌ Keine Ergebnisse")
                            
                    except ET.ParseError as e:
                        print(f"   ❌ XML Parse Error: {e}")
                        print(f"   Raw Response: {response.text[:300]}...")
                        
                else:
                    print(f"   ❌ HTTP Error: {response.text[:200]}...")
                    
            except Exception as e:
                print(f"   ❌ Exception: {e}")
        
        print(f"\n2. Gesamt-Zusammenfassung:")
        print(f"   Total gefundene Ergebnisse: {total_results}")
        
        if total_results == 0:
            print("   ❌ PROBLEM: Quasarr liefert keine Suchergebnisse!")
            print("   Mögliche Ursachen:")
            print("     - data-load.me ist nicht in Quasarr eingeloggt")
            print("     - Environment Variables wurden nicht richtig übernommen")
            print("     - data-load.me Hostname ist nicht konfiguriert")
            print("     - Netzwerk-Problem zwischen Container und data-load.me")
            
            # 3. Test ob überhaupt eine Quelle konfiguriert ist
            print("\n3. Teste Alternative Suchbegriffe...")
            simple_queries = ["test", "a", "2024"]
            
            for simple_q in simple_queries:
                print(f"   Einfache Suche: '{simple_q}'")
                simple_params = {
                    't': 'search',
                    'apikey': api_key,
                    'q': simple_q
                }
                
                simple_url = f"{base_url}/api?" + urlencode(simple_params)
                
                try:
                    simple_response = requests.get(simple_url, timeout=10)
                    if simple_response.status_code == 200:
                        simple_root = ET.fromstring(simple_response.text)
                        simple_items = simple_root.findall(".//item")
                        print(f"     → {len(simple_items)} Ergebnisse")
                        if len(simple_items) > 0:
                            break
                except:
                    pass
        else:
            print("   🎉 ERFOLG: data-load.me Integration funktioniert!")
        
        # 4. Test spezifische data-load.me URL Pattern
        print("\n4. Prüfe auf data-load.me spezifische Patterns...")
        
        # Test mit einem Begriff der garantiert auf data-load.me existiert
        dl_test_params = {
            't': 'search', 
            'apikey': api_key,
            'q': 'german',  # Sehr häufiger Begriff auf data-load.me
            'cat': '5000,2000'
        }
        
        dl_test_url = f"{base_url}/api?" + urlencode(dl_test_params)
        print(f"   URL: {dl_test_url}")
        
        try:
            dl_response = requests.get(dl_test_url, timeout=15)
            if dl_response.status_code == 200:
                dl_root = ET.fromstring(dl_response.text)
                dl_items = dl_root.findall(".//item")
                print(f"   German-Suche Ergebnisse: {len(dl_items)}")
                
                # Prüfe auf data-load.me Links
                dl_links_found = 0
                for item in dl_items:
                    link = item.find("link")
                    if link is not None and "data-load.me" in link.text:
                        dl_links_found += 1
                
                print(f"   data-load.me Links gefunden: {dl_links_found}")
                
                if dl_links_found == 0 and len(dl_items) > 0:
                    print("   ⚠️ Ergebnisse vorhanden, aber keine data-load.me Links!")
                    print("   Das bedeutet: Andere Quellen funktionieren, data-load.me nicht")
                    
        except Exception as e:
            print(f"   ❌ data-load.me Test Exception: {e}")
        
        print("\n=== DEBUG TEST ABGESCHLOSSEN ===")
        
    except Exception as e:
        print(f"❌ MAIN EXCEPTION: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Hauptfunktion"""
    
    print("Quasarr data-load.me Integration Tester")
    print("=======================================")
    print()
    
    base_url = "http://192.168.178.76:8080"  # Aus dem vorherigen Test
    api_key = "ae9f41cf2efbb752eb2734609bf93e9a7669801c9d7508828042a900da285566"  # Aus dem vorherigen Test
    
    print(f"Verwende URL: {base_url}")
    print(f"Verwende API Key: {api_key[:10]}...")
    print()
    
    test_quasarr_dl_debug(base_url, api_key)

if __name__ == "__main__":
    main() 