# -*- coding: utf-8 -*-
# Quasarr
# Project by https://github.com/rix1337
# DL Integration by oton15375

import html
import re
import time
from base64 import urlsafe_b64encode
from datetime import datetime, timedelta
import random
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from quasarr.providers.imdb_metadata import get_localized_title
from quasarr.providers.log import info, debug
def dl_flexible_string_match(search_string, title):
    """
    DL-spezifische flexible String-Matching-Funktion.
    Erkennt auch zusammengeschriebene Titel wie 'BetterCallSaulS01' für 'Better Call Saul'
    """
    from quasarr.providers.shared_state import sanitize_string
    
    sanitized_search_string = sanitize_string(search_string)
    sanitized_title = sanitize_string(title)

    # **FLEXIBLES MATCHING: Versuche verschiedene Strategien**
    
    # Strategie 1: Exakte Wort-Grenzen-Suche (bisherige Methode)
    if re.search(rf'\b{re.escape(sanitized_search_string)}\b', sanitized_title):
        debug(f"[DL-MATCH] Exact match: '{sanitized_search_string}' in '{sanitized_title}'")
        return True
    
    # Strategie 2: Flexibles Matching - entferne Leerzeichen aus beiden Strings
    search_no_spaces = sanitized_search_string.replace(' ', '')
    title_no_spaces = sanitized_title.replace(' ', '')
    
    if search_no_spaces and search_no_spaces in title_no_spaces:
        debug(f"[DL-MATCH] No-spaces match: '{search_no_spaces}' in '{title_no_spaces}'")
        return True
    
    # Strategie 3: Wort-für-Wort Matching - alle Wörter müssen vorkommen
    search_words = sanitized_search_string.split()
    if len(search_words) > 1:
        all_words_found = True
        for word in search_words:
            if len(word) >= 2 and word not in sanitized_title:  # Mindestens 2 Zeichen
                all_words_found = False
                break
        
        if all_words_found:
            debug(f"[DL-MATCH] Word-by-word match: '{sanitized_search_string}' in '{sanitized_title}'")
            return True
    
    # Kein Match gefunden
    debug(f"[DL-MATCH] No match: '{sanitized_search_string}' not found in '{sanitized_title}'")
    return False


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


def convert_to_rss_date(date_str):
    """Konvertiert ein Datum in das RSS-Format"""
    if not date_str:
        return datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z')
    
    try:
        # Versuche, das Datum zu parsen (je nach Format auf der Website)
        date = datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S')
    except ValueError:
        try:
            date = datetime.strptime(date_str, '%d %b %Y')
        except ValueError:
            # Fallback: aktuelles Datum
            date = datetime.now()
    
    # Konvertierung ins RSS-Format
    return date.strftime('%a, %d %b %Y %H:%M:%S %z')


def extract_search_id(session, user_agent):
    """Extrahiert die Such-ID aus der Hauptseite"""
    try:
        response = session.get("https://www.data-load.me", timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Suche nach Formularen oder Links, die zur Suchfunktion führen
        search_forms = soup.find_all('form', action=re.compile(r'/search/'))
        if search_forms:
            action_url = search_forms[0].get('action', '')
            search_id_match = re.search(r'/search/(\d+)/', action_url)
            if search_id_match:
                return search_id_match.group(1)
        
        # Suche nach Links
        search_links = soup.find_all('a', href=re.compile(r'/search/\d+/'))
        if search_links:
            href = search_links[0].get('href', '')
            search_id_match = re.search(r'/search/(\d+)/', href)
            if search_id_match:
                return search_id_match.group(1)
        
        # Fallback
        return "34811168"
    except Exception as e:
        debug(f"Fehler beim Extrahieren der Such-ID: {e}")
        return "34811168"


def dl_feed(shared_state, start_time, request_from):
    """Feed-Funktion für data-load.me - liefert Dummy-Releases für Sonarr-Indexer-Validierung"""
    releases = []
    dl = shared_state.values["config"]("Hostnames").get("dl")
    password = dl
    
    if not dl:
        debug("Hostname für DL nicht konfiguriert")
        return releases
    
    info(f"[DL-FEED] Dummy-Feed-Anfrage empfangen von {request_from}")
    
    # Bestimme welche Art von Content wir brauchen
    is_radarr = "Radarr" in request_from
    content_type = "Filme" if is_radarr else "Serien"
    info(f"[DL-FEED] Liefere Dummy-{content_type} für Indexer-Validierung")
    
    try:
        from datetime import datetime
        from base64 import urlsafe_b64encode
        
        # Erstelle Dummy-Releases für Indexer-Validierung
        if is_radarr:
            # Dummy-Filme für Radarr
            dummy_releases = [
                {
                    'title': 'The Matrix 1999 German DL 1080p BluRay x264-DUMMY',
                    'url': f'https://{dl}/threads/the-matrix-1999-german-dl-1080p-bluray-x264-dummy.123456/',
                    'size_bytes': 8 * 1024 * 1024 * 1024,  # 8GB
                },
                {
                    'title': 'Inception 2010 German DL 1080p BluRay x265-DUMMY',
                    'url': f'https://{dl}/threads/inception-2010-german-dl-1080p-bluray-x265-dummy.123457/',
                    'size_bytes': 6 * 1024 * 1024 * 1024,  # 6GB
                },
                {
                    'title': 'Interstellar 2014 German DL 2160p UHD BluRay x265-DUMMY',
                    'url': f'https://{dl}/threads/interstellar-2014-german-dl-2160p-uhd-bluray-x265-dummy.123458/',
                    'size_bytes': 15 * 1024 * 1024 * 1024,  # 15GB
                }
            ]
        else:
            # Dummy-Serien für Sonarr  
            dummy_releases = [
                {
                    'title': 'Breaking Bad S01 German DL 1080p BluRay x264-DUMMY',
                    'url': f'https://{dl}/threads/breaking-bad-s01-german-dl-1080p-bluray-x264-dummy.123459/',
                    'size_bytes': 12 * 1024 * 1024 * 1024,  # 12GB
                },
                {
                    'title': 'Better Call Saul S01 German DL 1080p BluRay x265-DUMMY', 
                    'url': f'https://{dl}/threads/better-call-saul-s01-german-dl-1080p-bluray-x265-dummy.123460/',
                    'size_bytes': 9 * 1024 * 1024 * 1024,  # 9GB
                },
                {
                    'title': 'Game of Thrones S01 German DL 1080p BluRay x264-DUMMY',
                    'url': f'https://{dl}/threads/game-of-thrones-s01-german-dl-1080p-bluray-x264-dummy.123461/',
                    'size_bytes': 18 * 1024 * 1024 * 1024,  # 18GB
                }
            ]
        
        info(f"[DL-FEED] Erstelle {len(dummy_releases)} Dummy-{content_type} für Indexer-Validierung")
        
        # Erstelle Release-Objekte aus Dummy-Daten
        for i, dummy_data in enumerate(dummy_releases):
            try:
                title = dummy_data['title']
                detail_url = dummy_data['url']
                size_bytes = dummy_data['size_bytes']
                
                # Datum (aktuelles Datum)
                published = datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0000')
                
                # Payload für JDownloader erstellen (Dummy-URL als Placeholder)
                payload = urlsafe_b64encode(f"{title}|{detail_url}|dl|{size_bytes//1024//1024}|{password}|".encode("utf-8")).decode("utf-8")
                jd_link = f"{shared_state.values['internal_address']}/download/?payload={payload}"
                
                releases.append({
                    "details": {
                        "title": f"[DL] {title}",
                        "imdb_id": "",
                        "link": jd_link,  # JDownloader-Link (für Downloads)
                        "size": size_bytes,
                        "date": published,
                        "source": detail_url  # Detail-URL (für Sonarr-Clicks)
                    },
                    "type": "protected"
                })
                
                debug(f"✓ Dummy-{content_type}: {title} ({size_bytes//1024//1024} MB)")
                
            except Exception as e:
                debug(f"Fehler beim Erstellen von Dummy-Release '{title}': {e}")
                continue
    
    except Exception as e:
        info(f"Fehler beim Laden des DL-Feeds: {e}")
    
    elapsed_time = time.time() - start_time
    info(f"[DL-FEED] {len(releases)} {content_type}-Releases in {elapsed_time:.2f} Sekunden gefunden")
    
    return releases


def dl_search(shared_state, start_time, request_from, search_string, season="", episode="", imdb_id=None):
    """Suche auf data-load.me"""
    releases = []
    dl = shared_state.values["config"]("Hostnames").get("dl")
    password = dl
    
    # **NEUE DEBUG-AUSGABE: Zeige was genau gesucht wird**
    info(f"[DL-DEBUG] Empfangen von {request_from}: Suchbegriff = '{search_string}', season = '{season}', episode = '{episode}', imdb_id = '{imdb_id}'")
    
    if not dl:
        debug("Hostname für DL nicht konfiguriert")
        return releases
    
    # **SMARTE SUCHLOGIK: Erstelle search_string wenn leer aber andere Parameter vorhanden**
    if not search_string and imdb_id:
        info(f"[DL-DEBUG] Leerer search_string, aber IMDb-ID '{imdb_id}' vorhanden - konvertiere zu Titel")
        search_string = get_localized_title(shared_state, imdb_id, 'de')
        if not search_string:
            info(f"[DL-DEBUG] FEHLER: Konnte keinen Titel aus IMDb-ID {imdb_id} extrahieren")
            return releases
        search_string = html.unescape(search_string)
        info(f"[DL-DEBUG] IMDb-ID {imdb_id} konvertiert zu Titel: '{search_string}'")
        
        # Erweitere mit Season/Episode falls vorhanden
        if season and episode:
            search_string = f"{search_string} S{int(season):02}E{int(episode):02}"
            info(f"[DL-DEBUG] Erweitert mit S{int(season):02}E{int(episode):02}: '{search_string}'")
        elif season:
            search_string = f"{search_string} S{int(season):02}"
            info(f"[DL-DEBUG] Erweitert mit S{int(season):02}: '{search_string}'")
    elif not search_string:
        info(f"[DL-DEBUG] Keine Suchparameter verfügbar - Suche abgebrochen")
        return releases
    
    # Überprüfen, ob es sich um eine IMDb-ID handelt (für den Fall dass search_string eine IMDb-ID ist)
    original_imdb_id = imdb_id
    if not imdb_id:
        imdb_id = shared_state.is_imdb_id(search_string)
    if imdb_id:
        info(f"[DL-DEBUG] IMDb-ID erkannt: {imdb_id} - konvertiere zu Titel...")
        search_string = get_localized_title(shared_state, imdb_id, 'de')
        if not search_string:
            info(f"[DL-DEBUG] FEHLER: Konnte keinen Titel aus IMDb-ID {imdb_id} extrahieren")
            return releases
        search_string = html.unescape(search_string)
        info(f"[DL-DEBUG] IMDb-ID {imdb_id} konvertiert zu Titel: '{search_string}'")
    else:
        info(f"[DL-DEBUG] Normale Textsuche: '{search_string}'")
    
    # Session mit Login abrufen (verwendet das neue intelligente Session-Management)
    from quasarr.downloads.sources.dl import get_persistent_session
    session = get_persistent_session(shared_state)
    
    # Session sollte immer verfügbar sein (entweder eingeloggt oder anonym)
    if not session:
        debug("[DL-SEARCH] KRITISCHER FEHLER: Keine Session verfügbar")
        return releases
    
    try:
        # Moderne Formular-Simulation (wie im Demo erfolgreich getestet)
        info(f"[DL-DEBUG] Starte Such-Formular-Simulation für: '{search_string}'")
        
        # SCHRITT 1: Lade die Such-Seite mit dem Suchbegriff
        initial_search_url = f"https://{dl}/search/?q={search_string}"
        debug(f"Lade Such-Seite: {initial_search_url}")
        
        search_page = session.get(initial_search_url, timeout=15)
        search_page.raise_for_status()
        
        # SCHRITT 2: Parse das Such-Formular
        soup = BeautifulSoup(search_page.text, 'html.parser')
        
        # Finde das Such-Formular
        search_form = None
        forms = soup.find_all('form')
        
        for form in forms:
            action = form.get('action', '')
            # Suche nach dem Such-Formular (hat keywords input oder /search action)
            if form.find('input', {'name': 'keywords'}) or '/search' in action:
                search_form = form
                break
        
        if not search_form:
            debug("Kein Such-Formular gefunden - Fallback zu alter Methode")
            # Fallback zur alten Methode
            search_id = extract_search_id(session, session.headers.get('User-Agent', 'Mozilla/5.0'))
            params = {
                'q': search_string,
                'c[title_only]': 1,
                'o': 'relevance'
            }
            search_url = f"https://{dl}/search/{search_id}/"
            response = session.get(search_url, params=params, timeout=10)
            response.raise_for_status()
        else:
            # SCHRITT 3: Sammle Formular-Daten
            form_action = search_form.get('action', '/search/search')
            if not form_action.startswith('http'):
                search_url = f"https://{dl}{form_action}"
            else:
                search_url = form_action
            
            # Sammle alle Input-Felder
            form_data = {}
            for input_field in search_form.find_all('input'):
                name = input_field.get('name')
                if not name:
                    continue
                
                input_type = input_field.get('type', 'text')
                value = input_field.get('value', '')
                
                # Setze Standardwerte
                if name == 'keywords':
                    value = search_string
                elif name == 'c[title_only]':
                    value = '1'  # Nur in Titeln suchen
                elif input_type == 'checkbox' and name not in ['c[title_only]']:
                    value = ''  # Andere Checkboxen nicht aktiviert
                
                form_data[name] = value
            
            # Konvertiere form_data zu URL-Parametern (nur nicht-leere Werte)
            get_params = {}
            for key, value in form_data.items():
                if value:
                    get_params[key] = value
            
            # SCHRITT 4: Sende Such-Request (verwende GET da POST oft fehlschlägt)
            debug(f"Führe Formular-Suche aus: {search_url}")
            
            # Kleine Verzögerung, um Erkennung als Bot zu vermeiden
            time.sleep(random.uniform(0.5, 1.5))
            
            response = session.get(search_url, params=get_params, timeout=15, allow_redirects=True)
        
        response.raise_for_status()
        info(f"[DL-DEBUG] Suchergebnisse geladen: {response.url}")
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Ergebnisse extrahieren - korrigierte data-load.me Struktur
        results = []
        
        # METHODE 1: Moderne data-load.me Struktur (block-row + contentRow)
        block_rows = soup.find_all('li', class_='block-row')
        info(f"[DL-DEBUG] Gefundene block-row Elemente: {len(block_rows)}")
        
        for row in block_rows:
            content_row = row.find('div', class_='contentRow')
            if content_row:
                results.append(content_row)
        
        # METHODE 2: Fallback für structItem-Struktur
        if not results:
            struct_items = soup.find_all('div', class_='structItem')
            info(f"[DL-DEBUG] Fallback: Gefundene structItem Elemente: {len(struct_items)}")
            results.extend(struct_items)
        
        # METHODE 3: Generischer Fallback für h3-Elemente mit Links
        if not results:
            h3_elements = soup.find_all('h3')
            info(f"[DL-DEBUG] Fallback: Gefundene h3 Elemente: {len(h3_elements)}")
            for h3 in h3_elements:
                if h3.find('a'):
                    results.append(h3.parent)
        
        # METHODE 4: Spezifische Suche nach Titel-Links mit dem Suchbegriff (zusätzlicher Fallback)
        if not results:
            sanitized_search = re.escape(search_string.lower())
            title_links = soup.find_all('a', string=re.compile(sanitized_search, re.IGNORECASE))
            info(f"[DL-DEBUG] Fallback: Gefundene titel-spezifische Links: {len(title_links)}")
            for link in title_links:
                parent = link.parent
                if parent.name in ['h3', 'h4', 'div']:
                    results.append(parent)
        
        info(f"[DL-DEBUG] Insgesamt extrahierte Such-Ergebnisse: {len(results)}")
        
        # Jetzt die Ergebnisse verarbeiten
        processed_count = 0
        for result in results:
            try:
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
                
                if not title_elem or not title_elem.text.strip():
                    continue
                
                # Titel bereinigen (HTML-Highlighting entfernen)
                title = title_elem.get_text(strip=True)
                title = html.unescape(title)
                
                # **DEBUG: Zeige jeden gefundenen Titel**
                debug(f"[DL-DEBUG] Gefundener Titel: '{title}'")
                
                # Überprüfen, ob der Suchbegriff im Titel enthalten ist
                if search_string and not dl_flexible_string_match(search_string, title):
                    debug(f"[DL-DEBUG] Titel '{title}' passt nicht zu Suchbegriff '{search_string}' - übersprungen")
                    continue
                
                debug(f"[DL-DEBUG] Titel '{title}' passt zu Suchbegriff '{search_string}' - wird verarbeitet")
                
                if not link:
                    continue
                
                # Relativen Link in absoluten umwandeln
                if not link.startswith(('http://', 'https://')):
                    link = urljoin(f"https://{dl}", link)
                
                # Größe extrahieren mit korrigierter Logik
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
                
                size_item = extract_size(size_text)
                mb = shared_state.convert_to_mb(size_item)
                
                # Datum extrahieren (falls verfügbar)
                date_elem = result.find(class_=['DateTime', 'date'])
                date_text = date_elem.text.strip() if date_elem else None
                published = convert_to_rss_date(date_text)
                
                # Link für JDownloader erstellen
                source = f"https://{dl}/"
                
                # WICHTIG: Hole den direkten Download-Link anstatt Thread-URL zu verwenden
                try:
                    debug(f"[DL-SEARCH] Versuche Download-Links für Thread-URL zu extrahieren: {link}")
                    from quasarr.downloads.sources.dl import get_all_download_links
                    download_links = get_all_download_links(shared_state, link)
                    debug(f"[DL-SEARCH] Gefundene Download-Links: {len(download_links) if download_links else 0}")
                    
                    # Verwende den ersten Download-Link falls verfügbar, sonst Thread-URL als Fallback
                    if download_links:
                        download_url = download_links[0]
                        debug(f"[DL-SEARCH] Download-Link für Payload: {download_url}")
                    else:
                        download_url = link
                        debug(f"[DL-SEARCH] Keine Download-Links gefunden, verwende Thread-URL: {download_url}")
                except Exception as e:
                    download_url = link
                    debug(f"[DL-SEARCH] Fehler beim Extrahieren der Download-Links ({str(e)}), verwende Thread-URL: {download_url}")
                    import traceback
                    debug(f"[DL-SEARCH] Traceback: {traceback.format_exc()}")
                
                payload = urlsafe_b64encode(f"{title}|{download_url}|dl|{mb*1024*1024}|{password}|{imdb_id}".encode("utf-8")).decode("utf-8")
                jd_link = f"{shared_state.values['internal_address']}/download/?payload={payload}"
                
                # Verbessere Titel für bessere Sonarr-Erkennung (wie in dl_search)
                formatted_title = title
                # Erkenne zusammengeschriebene Serien-Titel und formatiere sie besser
                # Beispiel: "BetterCallSaulS01" → "Better Call Saul S01" 
                # Beispiel: "AmericanDadS17" → "American Dad S17"
                
                season_pattern = r'([A-Z][a-z]+(?:[A-Z][a-z]+)*)(S\d{1,2}(?:E\d{1,2})?)'
                season_match = re.search(season_pattern, title)
                
                if season_match:
                    series_part = season_match.group(1)  # "BetterCallSaul" oder "AmericanDad"
                    season_part = season_match.group(2)  # "S01" oder "S17"
                    
                    # Füge Leerzeichen zwischen Großbuchstaben ein
                    spaced_series = re.sub(r'([a-z])([A-Z])', r'\1 \2', series_part)
                    
                    # Behalte den Rest des Titels (alles nach der Season)
                    rest_of_title = title[season_match.end():]
                    
                    formatted_title = f"{spaced_series} {season_part}{rest_of_title}"
                    debug(f"[DL-FEED-TITLE] Verbessert: '{title}' → '{formatted_title}'")
                    debug(f"[DL-FEED-TITLE] Details: series='{series_part}' → '{spaced_series}', season='{season_part}', rest='{rest_of_title}'")
                else:
                    # Fallback: Versuche auch andere Patterns zu erkennen
                    if re.match(r'[A-Z][a-z]+[A-Z]', title):
                        formatted_title = re.sub(r'([a-z])([A-Z])', r'\1 \2', title)
                        debug(f"[DL-FEED-TITLE] Fallback-Verbesserung: '{title}' → '{formatted_title}'")
                    else:
                        debug(f"[DL-FEED-TITLE] Keine Verbesserung möglich für: '{title}'")
                
                releases.append({
                    "details": {
                        "title": f"[DL] {formatted_title}",
                        "imdb_id": imdb_id,
                        "link": jd_link,  # JDownloader-Link (für Downloads)
                        "size": mb * 1024 * 1024,  # in Bytes
                        "date": published,
                        "source": download_url  # Detail-URL (für Sonarr-Clicks)
                    },
                    "type": "protected"
                })
            except Exception as e:
                debug(f"Fehler beim Parsen eines Suchergebnisses: {e}")
    
    except Exception as e:
        info(f"Fehler bei der DL-Suche: {e}")
    
    elapsed_time = time.time() - start_time
    debug(f"Zeit: {elapsed_time:.2f} Sekunden (dl)")
    
    return releases 