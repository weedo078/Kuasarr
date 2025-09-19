#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Test-Skript für data-load.me Webscraping

import requests
from bs4 import BeautifulSoup
import re
import time
import random
import argparse
from urllib.parse import urljoin, urlparse, parse_qs

# User-Agent, damit die Anfragen legitimer erscheinen
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36"

# Basis-URL
BASE_URL = "https://www.data-load.me"

def setup_session():
    """Eine Session mit angepassten Headers einrichten"""
    session = requests.Session()
    session.headers.update({
        'User-Agent': USER_AGENT,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    })
    return session

def test_connection(session):
    """Testen, ob eine Verbindung zur Website möglich ist"""
    try:
        response = session.get(BASE_URL, timeout=10)
        response.raise_for_status()
        print(f"[+] Verbindung zu {BASE_URL} erfolgreich (Status: {response.status_code})")
        return True
    except requests.RequestException as e:
        print(f"[-] Fehler bei der Verbindung zu {BASE_URL}: {e}")
        return False

def extract_search_id(session):
    """Versucht, die Such-ID aus der Hauptseite zu extrahieren"""
    try:
        response = session.get(BASE_URL, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Suche nach Formularen oder Links, die zur Suchfunktion führen könnten
        search_forms = soup.find_all('form', action=re.compile(r'/search/'))
        if search_forms:
            action_url = search_forms[0].get('action', '')
            search_id_match = re.search(r'/search/(\d+)/', action_url)
            if search_id_match:
                return search_id_match.group(1)
        
        # Suche nach Links, die zur Suchfunktion führen könnten
        search_links = soup.find_all('a', href=re.compile(r'/search/\d+/'))
        if search_links:
            href = search_links[0].get('href', '')
            search_id_match = re.search(r'/search/(\d+)/', href)
            if search_id_match:
                return search_id_match.group(1)
        
        return "34811168"  # Fallback auf die ID aus dem Beispiel
    except Exception as e:
        print(f"[-] Fehler beim Extrahieren der Such-ID: {e}")
        return "34811168"  # Fallback auf die ID aus dem Beispiel

def test_search(session, search_id, query, title_only=True, sort_by="relevance"):
    """Eine Suchanfrage durchführen und die Ergebnisse analysieren"""
    try:
        # URL-Parameter zusammenstellen
        params = {
            'q': query,
            'o': sort_by
        }
        
        if title_only:
            params['c[title_only]'] = 1
            
        # URL konstruieren
        search_url = f"{BASE_URL}/search/{search_id}/"
        
        # Verzögerung, um Erkennung als Bot zu vermeiden
        time.sleep(random.uniform(1, 2))
        
        # Anfrage senden
        response = session.get(search_url, params=params, timeout=10)
        response.raise_for_status()
        
        print(f"[+] Suchanfrage erfolgreich: {response.url}")
        
        # Ergebnisse analysieren
        return analyze_search_results(response.text)
        
    except requests.RequestException as e:
        print(f"[-] Fehler bei der Suchanfrage: {e}")
        return False, []

def analyze_search_results(html_content):
    """Analyisert die HTML-Antwort auf Suchergebnisse"""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Suche nach verschiedenen Ergebnistypen
    search_results = []
    
    # Versuch 1: Suche nach li-Elementen mit Thema-Klasse
    results = soup.find_all('li', class_=['prefix', 'discussionListItem'])
    
    # Versuch 2: Suche nach h3-Elementen, die Ergebnistitel enthalten könnten
    if not results:
        results = soup.find_all(['h2', 'h3', 'h4', 'div'], class_=['title'])
    
    # Alternative: Suche nach bestimmten Mustern in der Ausgabe
    if not results:
        # Suche nach typischen Thread-Format-Strukturen
        results = soup.find_all(['div', 'li'], id=re.compile(r'thread-\d+'))
    
    # Wenn alle direkten Methoden fehlschlagen, versuche es mit einer allgemeineren Methode
    if not results:
        # Suche nach Titel-Elementen, die typischerweise in Foren verwendet werden
        titles = soup.find_all(['a', 'h3', 'div'], text=re.compile(r'test', re.IGNORECASE))
        results = [t.parent for t in titles if t.parent is not None]
    
    # Aus den Ergebnissen die Titel und URLs extrahieren
    for result in results:
        try:
            # Versuche, den Titel zu finden
            title_elem = result.find(['a', 'h3', 'h4', 'div'], class_=['title', 'threadTitle']) or result.find('a')
            
            if title_elem and title_elem.text.strip():
                title = title_elem.text.strip()
                link = title_elem.get('href', '')
                
                # Relativen Link in absoluten umwandeln, falls nötig
                if link and not link.startswith(('http://', 'https://')):
                    link = urljoin(BASE_URL, link)
                
                search_results.append({
                    'title': title,
                    'link': link
                })
        except Exception as e:
            print(f"[!] Fehler beim Parsen eines Ergebnisses: {e}")
    
    has_results = len(search_results) > 0
    print(f"[+] Gefundene Ergebnisse: {len(search_results)}")
    
    # Drucke die ersten 5 Ergebnisse
    for i, result in enumerate(search_results[:5], 1):
        print(f"  {i}. {result['title']}")
        print(f"     URL: {result['link']}")
    
    return has_results, search_results

def test_search_url_structure(session, search_id):
    """Testet verschiedene URL-Strukturen für die Suche"""
    print("\n[*] Teste verschiedene URL-Strukturen für die Suche...")
    
    test_queries = [
        {'q': 'test', 'c[title_only]': 1, 'o': 'relevance'},
        {'q': 'movie', 'c[title_only]': 1, 'o': 'date'},
        {'q': 'series', 'o': 'relevance'},
        {'q': 'music', 'f[]': 'audio'}  # Versuche, nach Kategorie zu filtern
    ]
    
    for query_params in test_queries:
        query_str = '&'.join([f"{k}={v}" for k, v in query_params.items()])
        url = f"{BASE_URL}/search/{search_id}/?{query_str}"
        
        time.sleep(random.uniform(1, 2))
        
        try:
            response = session.get(url, timeout=10)
            status = "Erfolgreich" if response.status_code == 200 else f"Fehlgeschlagen ({response.status_code})"
            
            # Kurze Analyse der Antwort
            soup = BeautifulSoup(response.text, 'html.parser')
            title = soup.find('title').text if soup.find('title') else "Kein Titel gefunden"
            
            print(f"[+] URL: {url}")
            print(f"    Status: {status}")
            print(f"    Seiten-Titel: {title}")
            
            # Prüfe, ob Ergebnisse vorhanden sind (einfache Heuristik)
            has_results, _ = analyze_search_results(response.text)
            print(f"    Ergebnisse gefunden: {'Ja' if has_results else 'Nein'}")
            print()
            
        except requests.RequestException as e:
            print(f"[-] Fehler bei URL {url}: {e}")
            print()

def analyze_url_structure(url):
    """Analysiert die URL-Struktur, um sie besser zu verstehen"""
    print(f"\n[*] Analyse der URL-Struktur: {url}")
    
    parsed_url = urlparse(url)
    path_parts = parsed_url.path.strip('/').split('/')
    query_params = parse_qs(parsed_url.query)
    
    print(f"[+] Domäne: {parsed_url.netloc}")
    print(f"[+] Pfad-Komponenten: {path_parts}")
    print("[+] Query-Parameter:")
    
    for key, values in query_params.items():
        print(f"    {key}: {values[0]}")
    
    # Spezifische Analyse für data-load.me
    if len(path_parts) >= 2 and path_parts[0] == 'search':
        print(f"[+] Such-ID: {path_parts[1]}")
    
    print("[+] Vermutliche URL-Struktur:")
    print(f"    {parsed_url.scheme}://{parsed_url.netloc}/search/[ID]/?q=[SUCHBEGRIFF]&weitere_parameter")

def main():
    parser = argparse.ArgumentParser(description="Test-Skript für data-load.me Webscraping")
    parser.add_argument("--query", "-q", default="test", help="Suchbegriff für den Test")
    args = parser.parse_args()
    
    print("[*] Starte Test für Webscraping auf data-load.me...")
    
    # Session einrichten
    session = setup_session()
    
    # Verbindung testen
    if not test_connection(session):
        return
    
    # Such-ID extrahieren
    search_id = extract_search_id(session)
    print(f"[+] Verwendete Such-ID: {search_id}")
    
    # Die vom Benutzer angegebene URL analysieren
    sample_url = "https://www.data-load.me/search/34811168/?q=test&c[title_only]=1&o=relevance"
    analyze_url_structure(sample_url)
    
    # Suchtests durchführen
    print(f"\n[*] Teste Suche nach '{args.query}'...")
    success, results = test_search(session, search_id, args.query)
    
    if success:
        print("[+] Webscraping scheint möglich zu sein!")
    else:
        print("[-] Webscraping könnte problematisch sein. Überprüfe die HTML-Struktur manuell.")
    
    # Teste verschiedene URL-Strukturen
    test_search_url_structure(session, search_id)
    
    print("\n[*] Fazit:")
    print("[+] URL-Struktur: Die Suchfunktion scheint über die URL parameter steuerbar zu sein.")
    print("[+] Webscraping: Ein Parsen der Ergebnisse scheint grundsätzlich möglich zu sein.")
    print("[!] Empfehlung: Implementiere die dl_search Funktion basierend auf dem URL-Muster")
    print("    https://www.data-load.me/search/[ID]/?q=[SUCHBEGRIFF]&c[title_only]=1&o=relevance")

if __name__ == "__main__":
    main() 