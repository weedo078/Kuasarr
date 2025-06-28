# -*- coding: utf-8 -*-
# Quasarr
# Project by https://github.com/rix1337

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
    """Feed-Funktion für data-load.me - parst die /whats-new/ Seite nach echten Releases"""
    releases = []
    dl = shared_state.values["config"]("Hostnames").get("dl")
    password = dl
    
    if not dl:
        debug("Hostname für DL nicht konfiguriert")
        return releases
    
    info(f"[DL-SMART] Feed-Anfrage empfangen von {request_from}")
    
    # Bestimme welche Art von Content wir brauchen
    is_radarr = "Radarr" in request_from
    content_type = "Filme" if is_radarr else "Serien"
    info(f"[DL-FEED] Lade {content_type} für {request_from}")
    
    # Session mit Login abrufen
    from quasarr.downloads.sources.dl import create_and_persist_session
    session = create_and_persist_session(shared_state)
    
    if not session:
        debug("Konnte keine gültige DL-Session erstellen")
        return releases
    
    try:
        from datetime import datetime
        from base64 import urlsafe_b64encode
        import re
        
        # Lade die whats-new Seite
        feed_url = f"https://{dl}/whats-new/"
        debug(f"Lade Feed von: {feed_url}")
        
        response = session.get(feed_url, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Finde alle Thread-Links auf der Seite
        thread_links = soup.find_all('a', href=re.compile(r'/threads/'))
        debug(f"Gefundene Thread-Links: {len(thread_links)}")
        
        # **SCHRITT 1: Sammle passende Release-URLs**
        matching_releases = []
        processed_titles = set()
        
        # Definiere Content-Filter
        series_indicators = [
            r's\d{2}e\d{2}',  # S01E01 Format
            r'staffel\s+\d+',  # Staffel 1
            r'season\s+\d+',   # Season 1
            r'\bs\d{1,2}\b',   # S1, S01 etc.
            r'\d{1,2}x\d{1,2}',  # 1x01 Format
            'episode', 'folge', 'complete series', 'komplett', 'serie'
        ]
        
        movie_indicators = [
            r'\b(19|20)\d{2}\b',  # Jahreszahlen (1900-2099)
            'bluray', 'dvdrip', 'webrip', 'hdtv', 'film', 'movie'
        ]
        
        unwanted_indicators = [
            'xxx', 'porn', 'adult', 'musik', 'music', 'software', 
            'spiel', 'game', 'ebook', 'hörbuch', 'audiobook',
            'app', 'mobile', 'android', 'ios', 'dokumentation', 'doku'
        ]
        
        debug(f"Verarbeite {len(thread_links)} Thread-Links...")
        
        for link_elem in thread_links:
            try:
                href = link_elem.get('href', '')
                title = link_elem.get_text(strip=True)
                
                if not href or not title or len(title) < 5:
                    continue
                
                # Überspringe System-Links
                if any(skip in href.lower() for skip in ['/members/', '/categories/', '/tags/', '.rss']):
                    continue
                
                # Normalisiere Titel
                title = html.unescape(title).strip()
                if title in processed_titles:
                    continue
                
                title_lower = title.lower()
                
                # Überspringe unerwünschte Inhalte
                if any(unwanted in title_lower for unwanted in unwanted_indicators):
                    continue
                
                # Klassifiziere Content-Typ
                is_series = any(re.search(pattern, title_lower) for pattern in series_indicators)
                is_movie = any(re.search(pattern, title_lower) for pattern in movie_indicators)
                
                # Filtere basierend auf Anfrage-Typ
                if is_radarr and not is_movie:
                    continue  # Radarr will nur Filme
                elif not is_radarr and not is_series:
                    continue  # Sonarr will nur Serien
                
                processed_titles.add(title)
                
                # Erstelle vollständige URL
                if not href.startswith('http'):
                    full_url = f"https://{dl}{href}" if href.startswith('/') else f"https://{dl}/{href}"
                else:
                    full_url = href
                
                matching_releases.append({
                    'title': title,
                    'url': full_url,
                    'content_type': 'Film' if is_movie else 'Serie'
                })
                
                # Stoppe bei 30 passenden Releases
                if len(matching_releases) >= 30:
                    break
                    
            except Exception as e:
                debug(f"Fehler beim Sammeln von Release: {e}")
                continue
        
        info(f"[DL-FEED] {len(matching_releases)} passende {content_type} gefunden, lade Details...")
                
        # **SCHRITT 2: Lade Details für die ersten 30 passenden Releases**
        for i, release_info in enumerate(matching_releases):
            try:
                title = release_info['title']
                detail_url = release_info['url']
                
                debug(f"Lade Details für Release {i+1}/30: {title}")
                
                # Kleine Verzögerung zwischen Requests
                if i > 0:
                    time.sleep(random.uniform(0.3, 0.8))
                
                # Lade Detail-Seite
                detail_response = session.get(detail_url, timeout=10)
                detail_response.raise_for_status()
                detail_soup = BeautifulSoup(detail_response.text, "html.parser")
                
                # **EXTRAHIERE METADATEN AUS DER TABELLE**
                metadata = {}
                size_bytes = 1024 * 1024 * 1024  # Standard 1GB
                imdb_id = None
                
                # Suche nach Metadaten-Tabelle
                tables = detail_soup.find_all('table')
                for table in tables:
                    rows = table.find_all('tr')
                    for row in rows:
                        cells = row.find_all(['td', 'th'])
                        if len(cells) >= 2:
                            key = cells[0].get_text(strip=True).lower()
                            value = cells[1].get_text(strip=True)
                            
                            # Dateigröße extrahieren
                            if 'dateigröße' in key or 'size' in key or 'größe' in key:
                                try:
                                    # Parse Größenangaben wie "9.03 GB", "1.2 TB", "850 MB"
                                    size_match = re.search(r'([\d,\.]+)\s*(gb|mb|tb)', value.lower())
                                    if size_match:
                                        size_value = float(size_match.group(1).replace(',', '.'))
                                        unit = size_match.group(2)
                                        
                                        if unit == 'tb':
                                            size_bytes = int(size_value * 1024 * 1024 * 1024 * 1024)
                                        elif unit == 'gb':
                                            size_bytes = int(size_value * 1024 * 1024 * 1024)
                                        elif unit == 'mb':
                                            size_bytes = int(size_value * 1024 * 1024)
                                except:
                                    pass
                            
                            # IMDb-ID extrahieren
                            elif 'imdb' in key:
                                imdb_links = cells[1].find_all('a', href=re.compile(r'imdb\.com'))
                                if imdb_links:
                                    imdb_href = imdb_links[0].get('href', '')
                                    imdb_match = re.search(r'tt\d+', imdb_href)
                                    if imdb_match:
                                        imdb_id = imdb_match.group(0)
                
                # Datum (aktuelles Datum)
                published = datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0000')
                
                # Payload für JDownloader erstellen
                payload = urlsafe_b64encode(f"{title}|{detail_url}|{size_bytes//1024//1024}|{password}|{imdb_id or ''}".encode("utf-8")).decode("utf-8")
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
                        "size": size_bytes,
                        "date": published,
                        "source": detail_url  # Detail-URL (für Sonarr-Clicks)
                    },
                    "type": "protected"
                })
                
                debug(f"✓ {release_info['content_type']}: {title} ({size_bytes//1024//1024} MB)" + (f" [IMDB: {imdb_id}]" if imdb_id else ""))
                
            except Exception as e:
                debug(f"Fehler beim Laden von Details für '{title}': {e}")
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
    
    # Session mit Login abrufen
    from quasarr.downloads.sources.dl import create_and_persist_session
    session = create_and_persist_session(shared_state)
    
    if not session:
        debug("Konnte keine gültige DL-Session erstellen")
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
            
            # SCHRITT 4: Sende Such-Request (verwende GET da POST oft fehlschlägt)
            debug(f"Führe Formular-Suche aus: {search_url}")
            
            # Konvertiere form_data zu URL-Parametern (nur nicht-leere Werte)
            get_params = {}
            for key, value in form_data.items():
                if value:
                    get_params[key] = value
        
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
                payload = urlsafe_b64encode(f"{title}|{link}|{mb*1024*1024}|{password}|{imdb_id}".encode("utf-8")).decode("utf-8")
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
                        "source": link  # Detail-URL (für Sonarr-Clicks)
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