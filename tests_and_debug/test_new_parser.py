#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Test-Script für die neue Parser-Logik

from bs4 import BeautifulSoup
import re
import html

def debug(msg):
    print(f"[DEBUG] {msg}")

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

def extract_results_from_soup(soup):
    """
    Extrahiert Suchergebnisse/Feed-Ergebnisse aus data-load.me HTML
    Basierend auf der echten HTML-Struktur von data-load.me
    """
    results = []
    
    # METHODE 1: Moderne data-load.me Struktur (block-row + contentRow)
    # Das ist die aktuelle Struktur die wir in der Analyse gesehen haben
    block_rows = soup.find_all('li', class_='block-row')
    debug(f"Gefundene block-row Elemente: {len(block_rows)}")
    
    for row in block_rows:
        content_row = row.find('div', class_='contentRow')
        if content_row:
            results.append(content_row)
    
    # METHODE 2: Fallback für structItem-Struktur (aus anderen debug-Dateien gesehen)
    if not results:
        struct_items = soup.find_all('div', class_='structItem')
        debug(f"Fallback: Gefundene structItem Elemente: {len(struct_items)}")
        results.extend(struct_items)
    
    # METHODE 3: Generischer Fallback für h3-Elemente mit Links
    if not results:
        h3_elements = soup.find_all('h3')
        debug(f"Fallback: Gefundene h3 Elemente: {len(h3_elements)}")
        for h3 in h3_elements:
            if h3.find('a'):
                results.append(h3.parent)
    
    debug(f"Insgesamt extrahierte Ergebnisse: {len(results)}")
    return results

def extract_title_and_link_from_result(result):
    """
    Extrahiert Titel und Link aus einem Suchergebnis-Element
    """
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
        # Suche nach allen Links im Element
        all_links = result.find_all('a')
        for a_tag in all_links:
            href = a_tag.get('href', '')
            if '/threads/' in href and a_tag.text.strip():
                title_elem = a_tag
                link = href
                break
    
    if title_elem and title_elem.text.strip():
        # Entferne HTML-Tags und Highlighting aus dem Titel
        title = title_elem.get_text(strip=True)
        # Entferne HTML-Entities
        title = html.unescape(title)
        return title, link
    
    return None, None

def extract_size_from_result(result):
    """
    Extrahiert Größenangaben aus einem Suchergebnis-Element
    """
    size_text = ""
    
    # METHODE 1: Suche im contentRow-snippet
    snippet = result.find('div', class_='contentRow-snippet')
    if snippet:
        snippet_text = snippet.get_text()
        # Suche nach Größenangaben in verschiedenen Formaten
        size_match = re.search(r'Size:\s*(\d+(?:\.\d+)?)\s*([KMG]?B)', snippet_text, re.IGNORECASE)
        if size_match:
            size_text = f"{size_match.group(1)} {size_match.group(2)}"
    
    # METHODE 2: Allgemeine Suche nach Größenmustern im gesamten Element
    if not size_text:
        all_text = result.get_text()
        size_match = re.search(r'(\d+(?:\.\d+)?)\s*([KMG]?B)', all_text, re.IGNORECASE)
        if size_match:
            size_text = f"{size_match.group(1)} {size_match.group(2)}"
    
    return size_text

def test_with_saved_html():
    """Teste die neue Parser-Logik mit der gespeicherten HTML-Datei"""
    
    print("[*] === TEST DER NEUEN PARSER-LOGIK ===")
    
    # Lade die gespeicherte Suchseite
    try:
        with open('dataload_search_test.html', 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        soup = BeautifulSoup(html_content, 'html.parser')
        print("[+] HTML-Datei erfolgreich geladen")
        
        # Teste die neue Extraktions-Logik
        results = extract_results_from_soup(soup)
        
        if not results:
            print("[-] Keine Ergebnisse gefunden!")
            return
        
        print(f"[+] {len(results)} Ergebnisse gefunden")
        print()
        
        # Verarbeite die ersten 5 Ergebnisse
        for i, result in enumerate(results[:5]):
            print(f"[*] === ERGEBNIS {i+1} ===")
            
            # Titel und Link extrahieren
            title, link = extract_title_and_link_from_result(result)
            print(f"[+] Titel: {title}")
            print(f"[+] Link: {link}")
            
            # Größe extrahieren
            size_text = extract_size_from_result(result)
            if size_text:
                size_item = extract_size(size_text)
                print(f"[+] Größe: {size_item}")
            else:
                print("[-] Keine Größenangabe gefunden")
            
            print()
    
    except FileNotFoundError:
        print("[-] HTML-Datei 'dataload_search_test.html' nicht gefunden")
        print("    Führe erst 'analyze_dataload_structure.py' aus")

if __name__ == "__main__":
    test_with_saved_html() 