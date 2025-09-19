#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Finaler Debug für Feed-Ergebnisse

import os
import sys

def debug_final_feed():
    """Finaler Debug warum Login erfolgreich aber 0 Releases"""
    
    print("=== FINALER FEED DEBUG ===")
    
    # Environment Variables
    dl_user_env = os.environ.get('DL_USER')
    dl_password_env = os.environ.get('DL_PASSWORD')
    
    print(f"\nCredentials: {dl_user_env} / {dl_password_env[:2]}***")
    
    # Import
    try:
        from quasarr.downloads.sources.dl import create_and_persist_session
        from quasarr.search.sources.dl import dl_feed
        print("✅ Import erfolgreich")
    except ImportError as e:
        print(f"❌ Import-Fehler: {e}")
        return
    
    # VOLLSTÄNDIGER Mock
    class MockConfig:
        def __init__(self, values):
            self._values = values
        def get(self, key):
            return self._values.get(key)
    
    class MockSharedState:
        def __init__(self):
            self.storage = {}
            self.values = {
                "config": lambda section: {
                    "Hostnames": MockConfig({"dl": "data-load.me"}),
                    "DL": MockConfig({
                        "user": dl_user_env,
                        "password": dl_password_env,
                        "cookies": ""
                    })
                }.get(section, MockConfig({})),
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "internal_address": "http://192.168.178.76:8080"
            }
        
        def update(self, context, data):
            print(f"[MOCK] update(): context='{context}', data keys={list(data.keys()) if isinstance(data, dict) else type(data)}")
            self.storage[context] = data
        
        def get(self, context, default=None):
            result = self.storage.get(context, default)
            print(f"[MOCK] get(): context='{context}', result type={type(result)}")
            return result
            
        def convert_to_mb(self, size_str):
            """Mock für convert_to_mb"""
            if not size_str:
                return 0
            try:
                # Parse size strings like "1.5 GB", "500 MB", etc.
                size_str = size_str.strip().upper()
                if 'GB' in size_str:
                    return float(size_str.replace('GB', '').strip()) * 1024
                elif 'MB' in size_str:
                    return float(size_str.replace('MB', '').strip())
                elif 'KB' in size_str:
                    return float(size_str.replace('KB', '').strip()) / 1024
                else:
                    return 100  # Fallback
            except:
                return 100
    
    shared_state = MockSharedState()
    
    print(f"\n[1] Teste Session-Erstellung:")
    try:
        session = create_and_persist_session(shared_state)
        if session:
            print("  ✅ Session erfolgreich!")
            
            # Teste manuell eine Feed-URL
            print(f"\n[2] Teste Feed-URL direkt:")
            
            # Such-ID wie in dl_feed
            from quasarr.search.sources.dl import extract_search_id
            search_id = extract_search_id(session, session.headers.get('User-Agent', 'Mozilla/5.0'))
            feed_url = f"https://data-load.me/search/{search_id}/?o=date"
            
            print(f"  Feed-URL: {feed_url}")
            
            response = session.get(feed_url, timeout=10)
            print(f"  Status: {response.status_code}")
            print(f"  HTML-Länge: {len(response.text)} Zeichen")
            
            # HTML-Parsing testen
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, "html.parser")
            
            block_rows = soup.find_all('li', class_='block-row')
            print(f"  block-row Elemente: {len(block_rows)}")
            
            if block_rows:
                for i, row in enumerate(block_rows[:3]):
                    content_row = row.find('div', class_='contentRow')
                    if content_row:
                        title_elem = content_row.find('h3', class_='contentRow-title')
                        if title_elem:
                            title_link = title_elem.find('a')
                            if title_link:
                                title = title_link.get_text(strip=True)
                                print(f"    [{i+1}] {title[:50]}...")
            else:
                print("  ⚠️ Keine block-row Elemente - versuche Fallbacks")
                
                # Andere Strukturen testen
                struct_items = soup.find_all('div', class_='structItem')
                print(f"  structItem Elemente: {len(struct_items)}")
                
                all_links = soup.find_all('a')
                thread_links = [a for a in all_links if '/threads/' in a.get('href', '')]
                print(f"  Thread-Links gefunden: {len(thread_links)}")
                
                for i, link in enumerate(thread_links[:5]):
                    print(f"    [{i+1}] {link.get_text(strip=True)[:50]}...")
            
            print(f"\n[3] Teste dl_feed Funktion:")
            import time
            start_time = time.time()
            
            results = dl_feed(shared_state, start_time, "FinalTest")
            print(f"  ✅ dl_feed ausgeführt")
            print(f"  Ergebnisse: {len(results)}")
            
            if results:
                for i, result in enumerate(results[:3]):
                    details = result.get("details", {})
                    print(f"    [{i+1}] {details.get('title', 'Kein Titel')[:50]}...")
                    print(f"        Size: {details.get('size', 0)} bytes")
            else:
                print("  ⚠️ Keine Ergebnisse von dl_feed")
                
        else:
            print("  ❌ Session-Erstellung fehlgeschlagen")
            
    except Exception as e:
        print(f"  ❌ Fehler: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_final_feed() 