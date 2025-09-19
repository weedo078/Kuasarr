#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Debug-Script für data-load.me Feed-Ergebnisse

import requests
import time
from bs4 import BeautifulSoup
import re

def debug_dl_feed():
    """Debug warum dl_feed 0 Ergebnisse liefert"""
    
    print("=== DATA-LOAD.ME FEED DEBUG ===")
    
    # Credentials
    dl_hostname = "data-load.me"
    dl_user = "weedo078"
    dl_password = "zo-2!.ak"
    
    print(f"Hostname: {dl_hostname}")
    print(f"User: {dl_user}")
    print(f"Password: {'*' * len(dl_password)}")
    
    # Session Setup wie in dl_feed
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36',
    }
    
    session = requests.Session()
    session.headers.update(headers)
    
    # SCHRITT 1: Such-ID extrahieren (wie in dl_feed)
    print("\n[1] Extrahiere Such-ID...")
    try:
        response = session.get(f"https://{dl_hostname}", timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Suche nach Formularen oder Links, die zur Suchfunktion führen
        search_forms = soup.find_all('form', action=re.compile(r'/search/'))
        search_id = "34811168"  # Fallback
        
        if search_forms:
            action_url = search_forms[0].get('action', '')
            search_id_match = re.search(r'/search/(\d+)/', action_url)
            if search_id_match:
                search_id = search_id_match.group(1)
                print(f"    ✅ Such-ID aus Form: {search_id}")
            else:
                print(f"    ⚠️ Fallback Such-ID: {search_id}")
        else:
            print(f"    ⚠️ Keine Search-Forms gefunden, Fallback: {search_id}")
        
    except Exception as e:
        search_id = "34811168"
        print(f"    ❌ Fehler: {e}, verwende Fallback: {search_id}")
    
    # SCHRITT 2: Feed-URL testen (wie in dl_feed)
    print(f"\n[2] Teste Feed-URL...")
    try:
        feed_url = f"https://{dl_hostname}/search/{search_id}/?o=date"
        print(f"    URL: {feed_url}")
        
        response = session.get(feed_url, timeout=10)
        print(f"    Status: {response.status_code}")
        print(f"    Response-Länge: {len(response.text)} Zeichen")
        
        if response.status_code == 200:
            print("    ✅ Feed-URL erreichbar")
        else:
            print(f"    ❌ Fehler Status: {response.status_code}")
            return
            
    except Exception as e:
        print(f"    ❌ Verbindungsfehler: {e}")
        return
    
    # SCHRITT 3: HTML-Parsing testen (wie in dl_feed)
    print(f"\n[3] Analysiere HTML-Struktur...")
    try:
        soup = BeautifulSoup(response.text, "html.parser")
        
        # METHODE 1: Moderne data-load.me Struktur (block-row + contentRow)
        block_rows = soup.find_all('li', class_='block-row')
        print(f"    block-row Elemente: {len(block_rows)}")
        
        results = []
        for row in block_rows:
            content_row = row.find('div', class_='contentRow')
            if content_row:
                results.append(content_row)
        
        print(f"    contentRow Elemente: {len(results)}")
        
        # METHODE 2: Fallback für structItem-Struktur
        if not results:
            struct_items = soup.find_all('div', class_='structItem')
            print(f"    structItem Fallback: {len(struct_items)}")
            results.extend(struct_items)
        
        # METHODE 3: Generischer Fallback für h3-Elemente
        if not results:
            h3_elements = soup.find_all('h3')
            print(f"    h3 Fallback: {len(h3_elements)}")
            for h3 in h3_elements:
                if h3.find('a'):
                    results.append(h3.parent)
        
        print(f"    ✅ Insgesamt gefundene Elemente: {len(results)}")
        
        # SCHRITT 4: Parsen der ersten paar Ergebnisse
        if results:
            print(f"\n[4] Parse erste 3 Ergebnisse...")
            for i, result in enumerate(results[:3]):
                try:
                    # Titel extrahieren
                    title_elem = None
                    link = None
                    
                    # contentRow-Struktur
                    content_title = result.find('h3', class_='contentRow-title')
                    if content_title:
                        title_elem = content_title.find('a')
                        if title_elem:
                            link = title_elem.get('href', '')
                    
                    # structItem-Struktur
                    if not title_elem:
                        struct_title = result.find('div', class_='structItem-title')
                        if struct_title:
                            title_elem = struct_title.find('a')
                            if title_elem:
                                link = title_elem.get('href', '')
                    
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                        print(f"    [{i+1}] Titel: {title[:50]}...")
                        print(f"        Link: {link[:50]}...")
                        
                        # Größe extrahieren
                        snippet = result.find('div', class_='contentRow-snippet')
                        if snippet:
                            snippet_text = snippet.get_text()
                            size_match = re.search(r'Size:\s*(\d+(?:\.\d+)?)\s*([KMG]?B)', snippet_text, re.IGNORECASE)
                            if size_match:
                                size_text = f"{size_match.group(1)} {size_match.group(2)}"
                                print(f"        Größe: {size_text}")
                    else:
                        print(f"    [{i+1}] ❌ Kein Titel gefunden")
                        
                except Exception as e:
                    print(f"    [{i+1}] ❌ Parse-Fehler: {e}")
        else:
            print("\n[4] ❌ Keine Ergebnisse zum Parsen!")
            
            # Zeige erste 500 Zeichen der Antwort
            print("\n[DEBUG] Erste 500 Zeichen der Response:")
            print(response.text[:500])
            print("...")
            
    except Exception as e:
        print(f"    ❌ HTML-Parse-Fehler: {e}")

if __name__ == "__main__":
    debug_dl_feed() 