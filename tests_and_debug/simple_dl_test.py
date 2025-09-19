#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Einfacher direkter Test für dl.py Funktionen

import requests
from bs4 import BeautifulSoup
import re
import time
import random
import html

def extract_size(text):
    """Extrahiert die Größe aus einem Text"""
    if not text:
        return {"size": 0, "sizeunit": "B"}
    
    # Versuche, Größe im Format "123 MB" zu extrahieren
    match = re.search(r'(\d+(?:\.\d+)?)\s*([KMG]?B)', text, re.IGNORECASE)
    if match:
        size = float(match.group(1))
        unit = match.group(2).upper()
        return {"size": size, "sizeunit": unit}
    
    # Fallback: Annahme, dass keine Größenangabe vorhanden ist
    return {"size": 0, "sizeunit": "B"}

def debug(msg):
    print(f"[DEBUG] {msg}")

def info(msg):
    print(f"[INFO] {msg}")

def convert_to_mb(size_item):
    """Konvertiert Größenangaben zu MB"""
    if not size_item or size_item["size"] == 0:
        return 0
    
    size = size_item["size"]
    unit = size_item["sizeunit"].upper()
    
    if unit == "B":
        return size / (1024 * 1024)
    elif unit == "KB":
        return size / 1024
    elif unit == "MB":
        return size
    elif unit == "GB":
        return size * 1024
    else:
        return 0

def extract_search_id(session, user_agent):
    """Extrahiert die Such-ID von der data-load.me Startseite"""
    try:
        response = session.get("https://www.data-load.me/", timeout=10)
        response.raise_for_status()
        
        # Suche nach der Suche-Funktion
        match = re.search(r'/search/(\d+)/', response.text)
        if match:
            search_id = match.group(1)
            debug(f"Extrahierte Such-ID: {search_id}")
            return search_id
        
        # Fallback Such-ID
        fallback_id = "34811168"
        info(f"Konnte keine Such-ID finden, verwende Fallback: {fallback_id}")
        return fallback_id
        
    except Exception as e:
        debug(f"Fehler beim Extrahieren der Such-ID: {e}")
        return "34811168"

def test_dl_search_directly():
    """Teste die DL-Suchfunktion direkt"""
    
    print("[*] === DIREKTER TEST DER DL-SUCHFUNKTION ===")
    
    # Session einrichten
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36',
    }
    
    session = requests.Session()
    session.headers.update(headers)
    
    # Hostname
    dl = "www.data-load.me"
    search_string = "test"
    
    print(f"[+] Teste Suche nach: '{search_string}'")
    print(f"[+] Hostname: {dl}")
    
    # Such-ID extrahieren
    search_id = extract_search_id(session, headers['User-Agent'])
    
    try:
        # Suchparameter
        params = {
            'q': search_string,
            'c[title_only]': 1,  # Nur in Titeln suchen
            'o': 'relevance'  # Nach Relevanz sortieren
        }
        
        # URL konstruieren
        search_url = f"https://{dl}/search/{search_id}/"
        print(f"[+] Such-URL: {search_url}")
        print(f"[+] Parameter: {params}")
        
        # Kleine Verzögerung, um Erkennung als Bot zu vermeiden
        time.sleep(random.uniform(0.5, 1.5))
        
        # Anfrage senden
        response = session.get(search_url, params=params, timeout=10)
        response.raise_for_status()
        
        print(f"[+] Antwort erhalten (Status: {response.status_code})")
        print(f"[+] Finale URL: {response.url}")
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # NEUE PARSER-LOGIK ANWENDEN
        results = []
        
        # METHODE 1: Moderne data-load.me Struktur (block-row + contentRow)
        block_rows = soup.find_all('li', class_='block-row')
        debug(f"Gefundene block-row Elemente: {len(block_rows)}")
        
        for row in block_rows:
            content_row = row.find('div', class_='contentRow')
            if content_row:
                results.append(content_row)
        
        # METHODE 2: Fallback für structItem-Struktur
        if not results:
            struct_items = soup.find_all('div', class_='structItem')
            debug(f"Fallback: Gefundene structItem Elemente: {len(struct_items)}")
            results.extend(struct_items)
        
        debug(f"Insgesamt extrahierte Such-Ergebnisse: {len(results)}")
        
        if not results:
            print("[-] Keine Ergebnisse gefunden!")
            return
        
        print(f"[+] {len(results)} Ergebnisse gefunden")
        print()
        
        # Verarbeite die ersten 5 Ergebnisse
        for i, result in enumerate(results[:5]):
            print(f"[*] === ERGEBNIS {i+1} ===")
            
            # Titel und Link extrahieren mit korrigierter Logik
            title_elem = None
            link = None
            
            # METHODE 1: contentRow-Struktur (moderne data-load.me)
            content_title = result.find('h3', class_='contentRow-title')
            if content_title:
                title_elem = content_title.find('a')
                if title_elem:
                    link = title_elem.get('href', '')
            
            # METHODE 2: structItem-Struktur (alternative)
            if not title_elem:
                struct_title = result.find('div', class_='structItem-title')
                if struct_title:
                    title_elem = struct_title.find('a')
                    if title_elem:
                        link = title_elem.get('href', '')
            
            # METHODE 3: Generischer Fallback
            if not title_elem:
                all_links = result.find_all('a')
                for a_tag in all_links:
                    href = a_tag.get('href', '')
                    if '/threads/' in href and a_tag.text.strip():
                        title_elem = a_tag
                        link = href
                        break
            
            if title_elem and title_elem.text.strip():
                # Titel bereinigen (HTML-Highlighting entfernen)
                title = title_elem.get_text(strip=True)
                title = html.unescape(title)
                print(f"[+] Titel: {title}")
                print(f"[+] Link: {link}")
                
                # Größe extrahieren
                size_text = ""
                
                # Suche im contentRow-snippet
                snippet = result.find('div', class_='contentRow-snippet')
                if snippet:
                    snippet_text = snippet.get_text()
                    size_match = re.search(r'Size:\s*(\d+(?:\.\d+)?)\s*([KMG]?B)', snippet_text, re.IGNORECASE)
                    if size_match:
                        size_text = f"{size_match.group(1)} {size_match.group(2)}"
                
                # Fallback: Allgemeine Suche nach Größenmustern
                if not size_text:
                    all_text = result.get_text()
                    size_match = re.search(r'(\d+(?:\.\d+)?)\s*([KMG]?B)', all_text, re.IGNORECASE)
                    if size_match:
                        size_text = f"{size_match.group(1)} {size_match.group(2)}"
                
                if size_text:
                    size_item = extract_size(size_text)
                    mb = convert_to_mb(size_item)
                    print(f"[+] Größe: {size_item} ({mb:.2f} MB)")
                else:
                    print("[-] Keine Größenangabe gefunden")
            else:
                print("[-] Kein Titel gefunden")
            
            print()
    
    except Exception as e:
        print(f"[-] Fehler bei der Suche: {e}")

if __name__ == "__main__":
    test_dl_search_directly() 