#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quasarr API Testscript
Testet die API mit 50 echten Film- und Serien-Titeln zur Validierung der Integration
"""

import requests
import json
import time
import csv
from datetime import datetime
from xml.etree import ElementTree as ET

def get_user_input():
    """Fragt den Benutzer nach URL und API-Key"""
    print("=" * 60)
    print("QUASARR API TESTSCRIPT")
    print("=" * 60)
    print()
    
    base_url = input("Bitte geben Sie die Quasarr URL ein (z.B. http://localhost:8080): ").strip()
    if not base_url.startswith(('http://', 'https://')):
        base_url = 'http://' + base_url
    
    api_key = input("Bitte geben Sie den API-Key ein: ").strip()
    
    return base_url, api_key

def get_test_data():
    """Gibt eine Liste von 50 echten Film- und Serien-Titeln mit IMDb-IDs zurück"""
    test_data = [
        # Beliebte Filme
        {"title": "The Dark Knight", "imdb_id": "tt0468569", "type": "movie", "year": 2008},
        {"title": "Inception", "imdb_id": "tt1375666", "type": "movie", "year": 2010},
        {"title": "Pulp Fiction", "imdb_id": "tt0110912", "type": "movie", "year": 1994},
        {"title": "The Matrix", "imdb_id": "tt0133093", "type": "movie", "year": 1999},
        {"title": "Forrest Gump", "imdb_id": "tt0109830", "type": "movie", "year": 1994},
        {"title": "The Shawshank Redemption", "imdb_id": "tt0111161", "type": "movie", "year": 1994},
        {"title": "Goodfellas", "imdb_id": "tt0099685", "type": "movie", "year": 1990},
        {"title": "The Godfather", "imdb_id": "tt0068646", "type": "movie", "year": 1972},
        {"title": "Interstellar", "imdb_id": "tt0816692", "type": "movie", "year": 2014},
        {"title": "Fight Club", "imdb_id": "tt0137523", "type": "movie", "year": 1999},
        {"title": "Joker", "imdb_id": "tt7286456", "type": "movie", "year": 2019},
        {"title": "Avengers: Endgame", "imdb_id": "tt4154796", "type": "movie", "year": 2019},
        {"title": "The Wolf of Wall Street", "imdb_id": "tt0993846", "type": "movie", "year": 2013},
        {"title": "Parasite", "imdb_id": "tt6751668", "type": "movie", "year": 2019},
        {"title": "John Wick", "imdb_id": "tt2911666", "type": "movie", "year": 2014},
        {"title": "Mad Max: Fury Road", "imdb_id": "tt1392190", "type": "movie", "year": 2015},
        {"title": "Blade Runner 2049", "imdb_id": "tt1856101", "type": "movie", "year": 2017},
        {"title": "Once Upon a Time in Hollywood", "imdb_id": "tt7131622", "type": "movie", "year": 2019},
        {"title": "Django Unchained", "imdb_id": "tt1853728", "type": "movie", "year": 2012},
        {"title": "The Revenant", "imdb_id": "tt1663202", "type": "movie", "year": 2015},
        {"title": "Gladiator", "imdb_id": "tt0172495", "type": "movie", "year": 2000},
        {"title": "Casino Royale", "imdb_id": "tt0381061", "type": "movie", "year": 2006},
        {"title": "The Departed", "imdb_id": "tt0407887", "type": "movie", "year": 2006},
        {"title": "Avatar", "imdb_id": "tt0499549", "type": "movie", "year": 2009},
        {"title": "Dune", "imdb_id": "tt1160419", "type": "movie", "year": 2021},
        
        # Beliebte Serien
        {"title": "Breaking Bad", "imdb_id": "tt0903747", "type": "tv", "year": 2008},
        {"title": "Game of Thrones", "imdb_id": "tt0944947", "type": "tv", "year": 2011},
        {"title": "The Sopranos", "imdb_id": "tt0141842", "type": "tv", "year": 1999},
        {"title": "Better Call Saul", "imdb_id": "tt3110726", "type": "tv", "year": 2015},
        {"title": "Stranger Things", "imdb_id": "tt4574334", "type": "tv", "year": 2016},
        {"title": "The Office", "imdb_id": "tt0386676", "type": "tv", "year": 2005},
        {"title": "Friends", "imdb_id": "tt0108778", "type": "tv", "year": 1994},
        {"title": "The Wire", "imdb_id": "tt0306414", "type": "tv", "year": 2002},
        {"title": "Lost", "imdb_id": "tt0411008", "type": "tv", "year": 2004},
        {"title": "House of Cards", "imdb_id": "tt1856010", "type": "tv", "year": 2013},
        {"title": "Narcos", "imdb_id": "tt2707408", "type": "tv", "year": 2015},
        {"title": "The Crown", "imdb_id": "tt4786824", "type": "tv", "year": 2016},
        {"title": "Westworld", "imdb_id": "tt0475784", "type": "tv", "year": 2016},
        {"title": "True Detective", "imdb_id": "tt2356777", "type": "tv", "year": 2014},
        {"title": "Fargo", "imdb_id": "tt2802850", "type": "tv", "year": 2014},
        {"title": "The Mandalorian", "imdb_id": "tt8111088", "type": "tv", "year": 2019},
        {"title": "Ozark", "imdb_id": "tt5071412", "type": "tv", "year": 2017},
        {"title": "Mindhunter", "imdb_id": "tt5290382", "type": "tv", "year": 2017},
        {"title": "The Walking Dead", "imdb_id": "tt1520211", "type": "tv", "year": 2010},
        {"title": "Dexter", "imdb_id": "tt0773262", "type": "tv", "year": 2006},
        {"title": "Vikings", "imdb_id": "tt2306299", "type": "tv", "year": 2013},
        {"title": "Sherlock", "imdb_id": "tt1475582", "type": "tv", "year": 2010},
        {"title": "Black Mirror", "imdb_id": "tt2085059", "type": "tv", "year": 2011},
        {"title": "The Witcher", "imdb_id": "tt5180504", "type": "tv", "year": 2019},
        {"title": "Money Heist", "imdb_id": "tt6468322", "type": "tv", "year": 2017},
        {"title": "Dark", "imdb_id": "tt5753856", "type": "tv", "year": 2017},
        {"title": "Peaky Blinders", "imdb_id": "tt2442560", "type": "tv", "year": 2013},
        {"title": "The Boys", "imdb_id": "tt1190634", "type": "tv", "year": 2019},
        {"title": "Squid Game", "imdb_id": "tt10919420", "type": "tv", "year": 2021}
    ]
    
    return test_data

def test_api_connection(base_url, api_key):
    """Testet die Verbindung zur API mit dem Capabilities-Endpunkt"""
    print("Teste API-Verbindung...")
    
    url = f"{base_url}/api"
    params = {
        't': 'caps',
        'apikey': api_key
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        # Parse XML response
        root = ET.fromstring(response.text)
        server = root.find('.//server')
        
        if server is not None:
            title = server.get('title', 'Unbekannt')
            version = server.get('version', 'Unbekannt')
            print(f"✓ Verbindung erfolgreich! Server: {title} v{version}")
            return True
        else:
            print("✗ Unerwartete API-Antwort")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"✗ Verbindungsfehler: {e}")
        return False
    except ET.ParseError as e:
        print(f"✗ XML-Parsing-Fehler: {e}")
        return False

def search_content(base_url, api_key, title, imdb_id, content_type):
    """Führt eine Suchanfrage für einen bestimmten Titel durch"""
    
    # Bestimme den API-Modus basierend auf Content-Typ
    if content_type == "movie":
        mode = "movie"
        user_agent = "Radarr/3.2.2.5080"
    else:
        mode = "tvsearch"
        user_agent = "Sonarr/3.0.6.1196"
    
    url = f"{base_url}/api"
    params = {
        't': mode,
        'imdbid': imdb_id,
        'apikey': api_key
    }
    
    headers = {
        'User-Agent': user_agent
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Parse XML response
        root = ET.fromstring(response.text)
        items = root.findall('.//item')
        
        results = []
        for item in items:
            title_elem = item.find('title')
            link_elem = item.find('link')
            comments_elem = item.find('comments')
            size_elem = item.find('enclosure')
            guid_elem = item.find('guid')
            pubdate_elem = item.find('pubDate')
            
            if title_elem is not None and link_elem is not None:
                # Formatiere Größe in MB
                size_bytes = int(size_elem.get('length', '0')) if size_elem is not None else 0
                size_mb = round(size_bytes / (1024 * 1024), 2) if size_bytes > 0 else 0
                
                result = {
                    'title': title_elem.text if title_elem.text else '',
                    'download_link': link_elem.text if link_elem.text else '',
                    'thread_url': comments_elem.text if comments_elem is not None and comments_elem.text else '',
                    'guid': guid_elem.text if guid_elem is not None and guid_elem.text else '',
                    'size_bytes': size_bytes,
                    'size_mb': size_mb,
                    'pub_date': pubdate_elem.text if pubdate_elem is not None and pubdate_elem.text else ''
                }
                results.append(result)
        
        return {
            'success': True,
            'count': len(results),
            'results': results  # Alle Ergebnisse zurückgeben
        }
        
    except requests.exceptions.RequestException as e:
        return {
            'success': False,
            'error': f"Request-Fehler: {e}",
            'count': 0,
            'results': []
        }
    except ET.ParseError as e:
        return {
            'success': False,
            'error': f"XML-Parsing-Fehler: {e}",
            'count': 0,
            'results': []
        }

def run_tests(base_url, api_key, test_data):
    """Führt alle Tests durch und sammelt Ergebnisse"""
    print(f"\nStarte Tests mit {len(test_data)} Titeln...")
    print("=" * 60)
    
    results = []
    successful_searches = 0
    total_results_found = 0
    
    for i, data in enumerate(test_data, 1):
        print(f"[{i:2d}/50] Teste: {data['title']} ({data['year']}) - {data['type']}")
        
        search_result = search_content(
            base_url, 
            api_key, 
            data['title'], 
            data['imdb_id'], 
            data['type']
        )
        
        result = {
            'index': i,
            'title': data['title'],
            'imdb_id': data['imdb_id'],
            'type': data['type'],
            'year': data['year'],
            'success': search_result['success'],
            'count': search_result['count'],
            'error': search_result.get('error', ''),
            'all_results': search_result['results']
        }
        
        results.append(result)
        
        if search_result['success']:
            successful_searches += 1
            total_results_found += search_result['count']
            status = f"✓ {search_result['count']} Ergebnisse"
            
            # Zeige Details der ersten 3 Ergebnisse
            if search_result['results']:
                print(f"    {status}")
                for j, res in enumerate(search_result['results'][:3], 1):
                    print(f"      {j}. {res['title'][:60]}{'...' if len(res['title']) > 60 else ''}")
                    print(f"         Thread: {res['thread_url'][:80]}{'...' if len(res['thread_url']) > 80 else ''}")
                    print(f"         Download: {res['download_link'][:80]}{'...' if len(res['download_link']) > 80 else ''}")
                    print(f"         Größe: {res['size_mb']} MB")
                    print()
                if len(search_result['results']) > 3:
                    print(f"      ... und {len(search_result['results']) - 3} weitere Ergebnisse")
                    print()
        else:
            status = f"✗ {search_result.get('error', 'Unbekannter Fehler')}"
            print(f"    {status}")
            print()
        
        # Kurze Pause zwischen Anfragen
        time.sleep(0.5)
    
    return results, successful_searches, total_results_found

def generate_report(results, successful_searches, total_results_found):
    """Generiert einen detaillierten Bericht"""
    print("\n" + "=" * 60)
    print("TESTERGEBNISSE")
    print("=" * 60)
    
    total_tests = len(results)
    success_rate = (successful_searches / total_tests) * 100
    avg_results = total_results_found / successful_searches if successful_searches > 0 else 0
    
    print(f"Gesamte Tests: {total_tests}")
    print(f"Erfolgreich: {successful_searches}")
    print(f"Fehlgeschlagen: {total_tests - successful_searches}")
    print(f"Erfolgsquote: {success_rate:.1f}%")
    print(f"Gesamte Ergebnisse gefunden: {total_results_found}")
    print(f"Durchschnittliche Ergebnisse pro erfolgreicher Suche: {avg_results:.1f}")
    
    # Aufschlüsselung nach Content-Typ
    movie_results = [r for r in results if r['type'] == 'movie']
    tv_results = [r for r in results if r['type'] == 'tv']
    
    movie_success = sum(1 for r in movie_results if r['success'])
    tv_success = sum(1 for r in tv_results if r['success'])
    
    print(f"\nAufschlüsselung nach Typ:")
    print(f"Filme: {movie_success}/{len(movie_results)} ({(movie_success/len(movie_results)*100):.1f}%)")
    print(f"Serien: {tv_success}/{len(tv_results)} ({(tv_success/len(tv_results)*100):.1f}%)")
    
    # Top-Performer
    top_results = sorted([r for r in results if r['success']], key=lambda x: x['count'], reverse=True)[:5]
    if top_results:
        print(f"\nTop 5 Titel mit den meisten Ergebnissen:")
        for i, result in enumerate(top_results, 1):
            print(f"{i}. {result['title']} - {result['count']} Ergebnisse")
    
    # Überprüfung der Link-Qualität
    successful_with_results = [r for r in results if r['success'] and r['count'] > 0]
    results_with_thread_urls = 0
    results_with_download_links = 0
    
    for result in successful_with_results:
        for res in result['all_results']:
            if res.get('thread_url'):
                results_with_thread_urls += 1
            if res.get('download_link'):
                results_with_download_links += 1
    
    print(f"\nLink-Qualität:")
    print(f"Ergebnisse mit Thread-URLs: {results_with_thread_urls}/{total_results_found}")
    print(f"Ergebnisse mit Download-Links: {results_with_download_links}/{total_results_found}")
    
    # Fehlgeschlagene Suchen
    failed_results = [r for r in results if not r['success']]
    if failed_results:
        print(f"\nFehlgeschlagene Suchen ({len(failed_results)}):")
        for result in failed_results[:10]:  # Nur erste 10 anzeigen
            print(f"- {result['title']}: {result['error']}")
        if len(failed_results) > 10:
            print(f"  ... und {len(failed_results) - 10} weitere")

def save_detailed_results(results):
    """Speichert detaillierte Ergebnisse in CSV-Dateien"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Zusammenfassung-CSV
    summary_filename = f"quasarr_test_summary_{timestamp}.csv"
    
    with open(summary_filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['Index', 'Titel', 'IMDb_ID', 'Typ', 'Jahr', 'Erfolgreich', 'Anzahl_Ergebnisse', 'Fehler']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for result in results:
            writer.writerow({
                'Index': result['index'],
                'Titel': result['title'],
                'IMDb_ID': result['imdb_id'],
                'Typ': result['type'],
                'Jahr': result['year'],
                'Erfolgreich': 'Ja' if result['success'] else 'Nein',
                'Anzahl_Ergebnisse': result['count'],
                'Fehler': result['error']
            })
    
    # Detaillierte Ergebnisse-CSV mit allen gefundenen Releases
    details_filename = f"quasarr_test_details_{timestamp}.csv"
    
    with open(details_filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = [
            'Titel_Original', 'IMDb_ID', 'Typ', 'Jahr', 'Release_Index',
            'Release_Titel', 'Thread_URL', 'Download_Link', 'GUID', 
            'Groesse_MB', 'Groesse_Bytes', 'Veroeffentlicht'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for result in results:
            if result['success'] and result['all_results']:
                for i, release in enumerate(result['all_results'], 1):
                    writer.writerow({
                        'Titel_Original': result['title'],
                        'IMDb_ID': result['imdb_id'],
                        'Typ': result['type'],
                        'Jahr': result['year'],
                        'Release_Index': i,
                        'Release_Titel': release.get('title', ''),
                        'Thread_URL': release.get('thread_url', ''),
                        'Download_Link': release.get('download_link', ''),
                        'GUID': release.get('guid', ''),
                        'Groesse_MB': release.get('size_mb', ''),
                        'Groesse_Bytes': release.get('size_bytes', ''),
                        'Veroeffentlicht': release.get('pub_date', '')
                    })
    
    print(f"\nZusammenfassung gespeichert in: {summary_filename}")
    print(f"Detaillierte Ergebnisse gespeichert in: {details_filename}")
    print(f"\nDie Detail-CSV enthält alle Thread-URLs und Download-Links für manuelle Überprüfung.")

def main():
    try:
        # Benutzereingaben
        base_url, api_key = get_user_input()
        
        # API-Verbindung testen
        if not test_api_connection(base_url, api_key):
            print("Abbruch: API-Verbindung fehlgeschlagen")
            return
        
        # Testdaten laden
        test_data = get_test_data()
        
        # Tests durchführen
        start_time = time.time()
        results, successful_searches, total_results_found = run_tests(base_url, api_key, test_data)
        end_time = time.time()
        
        # Bericht generieren
        generate_report(results, successful_searches, total_results_found)
        
        print(f"\nGesamte Testdauer: {end_time - start_time:.1f} Sekunden")
        
        # Ergebnisse speichern
        save_detailed_results(results)
        
        print("\nTest abgeschlossen!")
        
    except KeyboardInterrupt:
        print("\n\nTest durch Benutzer abgebrochen.")
    except Exception as e:
        print(f"\nUnerwarteter Fehler: {e}")

if __name__ == "__main__":
    main() 