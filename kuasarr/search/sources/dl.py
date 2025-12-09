# -*- coding: utf-8 -*-
# Kuasarr
# Project by weedo078 (Fork von https://github.com/rix1337/Quasarr)
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

from kuasarr.providers.imdb_metadata import get_localized_title
from kuasarr.providers.log import info, debug
from kuasarr.providers.sessions.dl import fetch_via_requests_session

def dl_flexible_string_match(search_string, title):
    """
    DL-spezifische flexible String-Matching-Funktion.
    Erkennt auch zusammengeschriebene Titel wie 'BetterCallSaulS01' für 'Better Call Saul'
    """
    from kuasarr.providers.shared_state import sanitize_string
    
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


def extract_size_from_text(text):
    """
    Erweiterte Größenextraktion aus verschiedenen Text-Formaten
    Basierend auf den HTML-Beispielen von data-load.me
    """
    if not text:
        return {"size": 0, "sizeunit": "B"}
    
    # Normalisiere den Text für bessere Erkennung
    text = text.strip()
    
    debug(f"[DL-SIZE] Analysiere Text: {text[:200]}...")
    
    # SPEZIAL-CHECK: Multi-Größen Format mit "je" - Muss ZUERST kommen!
    if "je " in text.lower():
        all_sizes = re.findall(r'(\d+(?:[.,]\d+)?)\s*([KMGT]?i?B)', text, re.IGNORECASE)
        if len(all_sizes) > 1:
            # Konvertiere alle zu MB und nehme die größte
            best_size = 0
            best_unit = "B"
            best_original = 0
            
            for size_str, unit in all_sizes:
                size = float(size_str.replace(',', '.'))
                clean_unit = unit.upper().replace('IB', 'B')
                
                # Konvertiere zu MB für Vergleich
                mb_value = size
                if clean_unit == "KB":
                    mb_value = size / 1024
                elif clean_unit == "GB":
                    mb_value = size * 1024
                elif clean_unit == "TB":
                    mb_value = size * 1024 * 1024
                
                if mb_value > best_size:
                    best_size = mb_value
                    best_unit = clean_unit
                    best_original = size
            
            if best_size > 0:
                debug(f"[DL-SIZE] Multi-Format mit 'je' gefunden: {best_original} {best_unit} (größte von {len(all_sizes)} Größen)")
                return {"size": best_original, "sizeunit": best_unit}
    
    # Methode 1: MediaInfo "File size" Format aus Code-Blöcken
    # "File size                                : 926 MiB"
    size_match = re.search(r'File\s+size\s*[:ï¼š]\s*(\d+(?:[.,]\d+)?)\s*([KMGT]?i?B)', text, re.IGNORECASE)
    if size_match:
        size_str = size_match.group(1).replace(',', '.')
        size = float(size_str)
        unit = size_match.group(2).upper().replace('IB', 'B')  # MiB -> MB
        debug(f"[DL-SIZE] MediaInfo File size gefunden: {size} {unit}")
        return {"size": size, "sizeunit": unit}
    
    # Methode 2: "FileSize" Format mit Punkten
    # "FileSize......: 6.66 GiB"
    size_match = re.search(r'FileSize[.\s]*[:ï¼š]\s*(\d+(?:[.,]\d+)?)\s*([KMGT]?i?B)', text, re.IGNORECASE)
    if size_match:
        size_str = size_match.group(1).replace(',', '.')
        size = float(size_str)
        unit = size_match.group(2).upper().replace('IB', 'B')  # GiB -> GB
        debug(f"[DL-SIZE] FileSize-Format gefunden: {size} {unit}")
        return {"size": size, "sizeunit": unit}
    
    # Methode 3: Einfaches "size:" Format
    # "size: 2.0 GiB"
    size_match = re.search(r'\bsize\s*[:ï¼š]\s*(\d+(?:[.,]\d+)?)\s*([KMGT]?i?B)', text, re.IGNORECASE)
    if size_match:
        size_str = size_match.group(1).replace(',', '.')
        size = float(size_str)
        unit = size_match.group(2).upper().replace('IB', 'B')
        debug(f"[DL-SIZE] Size-Format gefunden: {size} {unit}")
        return {"size": size, "sizeunit": unit}
    
    # Methode 4: "Größe" oder "Grösse" Format (deutsche Varianten)
    # "Grösse.............: je 721 MB 1,23 GB" oder "Größe: 5.67 GB"
    # WICHTIG: Bei "je" Format mit mehreren Größen, gehe zu Multi-Format
    size_match = re.search(r'Gr[öo](?:ss|ß)e[.\s]*[:ï¼š]\s*(?!je\s)(\d+(?:[.,]\d+)?)\s*([KMGT]?i?B)', text, re.IGNORECASE)
    if size_match:
        size_str = size_match.group(1).replace(',', '.')
        size = float(size_str)
        unit = size_match.group(2).upper().replace('IB', 'B')
        debug(f"[DL-SIZE] Größe-Format gefunden: {size} {unit}")
        return {"size": size, "sizeunit": unit}
    
    # Methode 5: Standard Format ohne Doppelpunkt
    # "123 MB" oder "123.45 GB"
    size_match = re.search(r'\b(\d+(?:[.,]\d+)?)\s*([KMGT]?i?B)\b', text, re.IGNORECASE)
    if size_match:
        size_str = size_match.group(1).replace(',', '.')
        size = float(size_str)
        unit = size_match.group(2).upper().replace('IB', 'B')
        debug(f"[DL-SIZE] Standard-Format gefunden: {size} {unit}")
        return {"size": size, "sizeunit": unit}
    
    # Methode 6: Größe in Klammern oder als separater Text
    # "[123 MB]" oder "(1.5 GB)"
    size_match = re.search(r'[\[\(](\d+(?:[.,]\d+)?)\s*([KMGT]?i?B)[\]\)]', text, re.IGNORECASE)
    if size_match:
        size_str = size_match.group(1).replace(',', '.')
        size = float(size_str)
        unit = size_match.group(2).upper().replace('IB', 'B')
        debug(f"[DL-SIZE] Klammer-Format gefunden: {size} {unit}")
        return {"size": size, "sizeunit": unit}
    
    # Methode 7: Spezielle Formate mit HTML-Tags
    # Entferne HTML-Tags für bessere Erkennung
    clean_text = re.sub(r'<[^>]+>', ' ', text)
    if clean_text != text:
        debug(f"[DL-SIZE] Versuche nochmal ohne HTML-Tags")
        return extract_size_from_text(clean_text)
    
    # Methode 8: Multi-Größen Format (nehme die erste größere Größe)
    # "je 721 MB 1,23 GB" - nehme 1,23 GB
    all_sizes = re.findall(r'(\d+(?:[.,]\d+)?)\s*([KMGT]?i?B)', text, re.IGNORECASE)
    if all_sizes:
        # Konvertiere alle zu MB und nehme die größte
        best_size = 0
        best_unit = "B"
        best_original = 0
        
        for size_str, unit in all_sizes:
            size = float(size_str.replace(',', '.'))
            clean_unit = unit.upper().replace('IB', 'B')
            
            # Konvertiere zu MB für Vergleich
            mb_value = size
            if clean_unit == "KB":
                mb_value = size / 1024
            elif clean_unit == "GB":
                mb_value = size * 1024
            elif clean_unit == "TB":
                mb_value = size * 1024 * 1024
            
            if mb_value > best_size:
                best_size = mb_value
                best_unit = clean_unit
                best_original = size
        
        if best_size > 0:
            debug(f"[DL-SIZE] Multi-Format gefunden: {best_original} {best_unit} (größte von {len(all_sizes)} Größen)")
            return {"size": best_original, "sizeunit": best_unit}
    
    # Fallback: Keine Größe gefunden
    debug(f"[DL-SIZE] Keine Größenangabe gefunden in: {text[:100]}...")
    return {"size": 0, "sizeunit": "B"}


def extract_size(text):
    """Extrahiert die Größe aus einem Text (Legacy-Funktion)"""
    return extract_size_from_text(text)


def parse_date_from_html(html_elem):
    """
    Erweiterte Datumsextraktion aus HTML-Elementen
    Basierend auf den HTML-Beispielen von data-load.me
    """
    if not html_elem:
        return None
    
    # Methode 1: <time> Element mit datetime Attribut
    time_elem = html_elem.find('time', class_='u-dt')
    if time_elem:
        datetime_str = time_elem.get('datetime')
        if datetime_str:
            try:
                # Parse ISO format: 2025-01-18T14:06:58+0100
                # Entferne Zeitzone-Info für einfaches Parsing
                if '+' in datetime_str:
                    datetime_clean = datetime_str.split('+')[0]
                elif datetime_str.count('-') > 2:  # Mehr als 2 Bindestriche = Zeitzone
                    datetime_clean = datetime_str.rsplit('-', 1)[0]
                else:
                    datetime_clean = datetime_str
                
                parsed_date = datetime.fromisoformat(datetime_clean)
                formatted_date = parsed_date.strftime('%a, %d %b %Y %H:%M:%S +0000')
                debug(f"[DL-DATE] Zeit-Element gefunden: {formatted_date} (von {datetime_str})")
                return formatted_date
            except Exception as e:
                debug(f"[DL-DATE] Fehler beim Parsen von datetime '{datetime_str}': {e}")
    
    # Methode 2: <time> Element mit data-time Attribut (Unix Timestamp)
    if time_elem and time_elem.get('data-time'):
        try:
            timestamp = int(time_elem.get('data-time'))
            parsed_date = datetime.fromtimestamp(timestamp)
            formatted_date = parsed_date.strftime('%a, %d %b %Y %H:%M:%S +0000')
            debug(f"[DL-DATE] Unix-Timestamp gefunden: {formatted_date} (von {timestamp})")
            return formatted_date
        except Exception as e:
            debug(f"[DL-DATE] Fehler beim Parsen von data-time: {e}")
    
    # Methode 3: Text-Datum im time Element
    if time_elem and time_elem.text:
        date_text = time_elem.text.strip()
        try:
            # Deutsche Datumsformate: "18 Januar 2025"
            if re.match(r'\d{1,2}\s+\w+\s+\d{4}', date_text):
                # Konvertiere deutsche Monatsnamen
                month_map = {
                    'Januar': 'January', 'Februar': 'February', 'März': 'March',
                    'April': 'April', 'Mai': 'May', 'Juni': 'June',
                    'Juli': 'July', 'August': 'August', 'September': 'September',
                    'Oktober': 'October', 'November': 'November', 'Dezember': 'December'
                }
                
                english_date = date_text
                for german, english in month_map.items():
                    english_date = english_date.replace(german, english)
                
                parsed_date = datetime.strptime(english_date, '%d %B %Y')
                formatted_date = parsed_date.strftime('%a, %d %b %Y %H:%M:%S +0000')
                debug(f"[DL-DATE] Text-Datum gefunden: {formatted_date} (von '{date_text}')")
                return formatted_date
        except Exception as e:
            debug(f"[DL-DATE] Fehler beim Parsen von Text-Datum '{date_text}': {e}")
    
    # Methode 4: Suche nach beliebigen time-Elementen im Element
    all_time_elems = html_elem.find_all('time')
    for time_elem in all_time_elems:
        result = parse_date_from_html(time_elem.parent if time_elem.parent else time_elem)
        if result:
            return result
    
    debug("[DL-DATE] Kein gültiges Datum gefunden")
    return None


def convert_to_rss_date(date_str):
    """Konvertiert ein Datum in das RSS-Format"""
    if not date_str:
        return datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0000')
    
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
    return date.strftime('%a, %d %b %Y %H:%M:%S +0000')


def extract_search_id(shared_state):
    """Extrahiert die Such-ID aus der Hauptseite"""
    try:
        response = fetch_via_requests_session(shared_state, "GET", "https://www.data-load.me", timeout=10)
        if not response:
            return "34811168"
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


def dl_feed(shared_state, start_time, request_from, mirror=None):
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
                        "title": title,
                        "hostname": "dl",
                        "mirror": mirror,
                        "imdb_id": "",
                        "link": jd_link,  # JDownloader-Link (für Downloads)
                        "size": size_bytes,
                        "date": published,
                        "source": detail_url  # Detail-URL (für Sonarr-Clicks)
                    },
                    "type": "protected"
                })
                
                debug(f"âœ“ Dummy-{content_type}: {title} ({size_bytes//1024//1024} MB)")
                
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
    
    try:
        # Moderne Formular-Simulation (wie im Demo erfolgreich getestet)
        info(f"[DL-DEBUG] Starte Such-Formular-Simulation für: '{search_string}'")
        
        # SCHRITT 1: Lade die Such-Seite mit dem Suchbegriff
        initial_search_url = f"https://{dl}/search/?q={search_string}"
        debug(f"Lade Such-Seite: {initial_search_url}")
        
        search_page = fetch_via_requests_session(shared_state, "GET", initial_search_url, timeout=15)
        if not search_page:
            debug("[DL-SEARCH] KRITISCHER FEHLER: Konnte Such-Seite nicht laden")
            return releases
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
            search_id = extract_search_id(shared_state)
            from urllib.parse import urlencode
            params = {
                'q': search_string,
                'c[title_only]': 1,
                'o': 'relevance'
            }
            search_url = f"https://{dl}/search/{search_id}/?{urlencode(params)}"
            response = fetch_via_requests_session(shared_state, "GET", search_url, timeout=10)
            if not response:
                debug("[DL-SEARCH] KRITISCHER FEHLER: Konnte Fallback-Suche nicht ausführen")
                return releases
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
            
            # URL mit Parametern zusammenbauen
            if get_params:
                from urllib.parse import urlencode
                if '?' in search_url:
                    full_url = f"{search_url}&{urlencode(get_params)}"
                else:
                    full_url = f"{search_url}?{urlencode(get_params)}"
            else:
                full_url = search_url
            
            response = fetch_via_requests_session(shared_state, "GET", full_url, timeout=15)
            if not response:
                debug("[DL-SEARCH] KRITISCHER FEHLER: Konnte Formular-Suche nicht ausführen")
                return releases
        
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
                
                # Überprüfen, ob der Suchbegriff im Titel enthalten ist
                if search_string and not dl_flexible_string_match(search_string, title):
                    continue
                
                if not link:
                    continue
                
                # Relativen Link in absoluten umwandeln
                if not link.startswith(('http://', 'https://')):
                    link = urljoin(f"https://{dl}", link)
                
                # **VERBESSERTE GRÖSSEN-EXTRAKTION**
                size_text = ""
                mb = 0
                
                # Suche ZUERST im spezifischen Thread-Content, nicht in übergeordneten Elementen
                
                # 1. Versuche direkt zur Thread-Seite zu gehen für spezifische Größenangaben
                thread_size_found = False
                
                # Schaue ob es ein Link zu einem spezifischen Thread gibt
                if link and '/threads/' in link:
                    try:
                        debug(f"[DL-SIZE] Versuche Thread-spezifische Größensuche für: {link}")
                        thread_response = fetch_via_requests_session(shared_state, "GET", link, timeout=10)
                        if thread_response and thread_response.status_code == 200:
                            thread_soup = BeautifulSoup(thread_response.text, 'html.parser')
                            
                            # Suche in Thread-spezifischen Bereichen nach Größenangaben
                            thread_size_sources = []
                            
                            # In bbCodeBlock-content divs (häufig für Größenangaben in Threads)
                            bbcode_blocks = thread_soup.find_all('div', class_='bbCodeBlock-content')
                            for block in bbcode_blocks:
                                thread_size_sources.append(block.get_text())
                            
                            # In pre-Elementen (für formatierte Info-Blöcke)
                            pre_blocks = thread_soup.find_all('pre')
                            for pre in pre_blocks:
                                thread_size_sources.append(pre.get_text())
                            
                            # In messageContent divs (Post-Inhalte)
                            message_blocks = thread_soup.find_all('div', class_=['message-userContent', 'messageContent'])
                            for block in message_blocks:
                                thread_size_sources.append(block.get_text())
                            
                            debug(f"[DL-SIZE] Thread-spezifische Suche in {len(thread_size_sources)} Bereichen")
                            
                            for i, source_text in enumerate(thread_size_sources):
                                if not source_text:
                                    continue
                                    
                                size_info = extract_size_from_text(source_text)
                                if size_info["size"] > 0:
                                    size_text = f"{size_info['size']} {size_info['sizeunit']}"
                                    mb = shared_state.convert_to_mb(size_info)
                                    debug(f"[DL-SIZE] Thread-spezifisch gefunden in Bereich {i}: {size_text} = {mb} MB")
                                    thread_size_found = True
                                    break
                            
                            if thread_size_found:
                                debug(f"[DL-SIZE] Thread-spezifische Größe erfolgreich: {size_text}")
                            else:
                                debug(f"[DL-SIZE] Keine thread-spezifische Größe gefunden")
                    except Exception as e:
                        debug(f"[DL-SIZE] Fehler bei thread-spezifischer Suche: {e}")
                
                # 2. Fallback: Suche nur im aktuellen Suchergebnis-Element (NICHT in parent-Elementen)
                if not thread_size_found:
                    debug(f"[DL-SIZE] Fallback: Suche nur im Suchergebnis-Element")
                    
                    # Nur im aktuellen Result-Element suchen
                    current_text = result.get_text()
                    size_info = extract_size_from_text(current_text)
                    if size_info["size"] > 0:
                        size_text = f"{size_info['size']} {size_info['sizeunit']}"
                        mb = shared_state.convert_to_mb(size_info)
                        debug(f"[DL-SIZE] Fallback erfolgreich: {size_text} = {mb} MB")
                    else:
                        debug(f"[DL-SIZE] Auch im Fallback keine Größe gefunden")
                        # Setze auf 0, damit nicht die falsche Größe angezeigt wird
                        mb = 0
                
                # **VERBESSERTE DATUMS-EXTRAKTION**
                published = None
                
                # Suche nach Datums-Elementen in verschiedenen Bereichen
                date_contexts = [result]
                
                # Erweitere Suchbereich um parent-Elemente
                current = result
                for _ in range(3):
                    if hasattr(current, 'parent') and current.parent:
                        current = current.parent
                        date_contexts.append(current)
                    else:
                        break
                
                debug(f"[DL-DATE] Suche Datum in {len(date_contexts)} HTML-Kontexten")
                
                for i, context in enumerate(date_contexts):
                    parsed_date = parse_date_from_html(context)
                    if parsed_date:
                        published = parsed_date
                        debug(f"[DL-DATE] Erfolg in Kontext {i}: {published}")
                        break
                    else:
                        debug(f"[DL-DATE] Kontext {i}: Kein Datum gefunden")
                
                # Fallback auf aktuelles Datum
                if not published:
                    published = datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0000')
                    debug(f"[DL-DATE] Fallback auf aktuelles Datum: {published}")
                
                # Link für JDownloader erstellen
                source = f"https://{dl}/"
                
                # WICHTIG: Verwende immer die Thread-URL im Payload, nicht den Download-Link!
                # Der Download-Handler holt sich die Links selbst basierend auf der Thread-URL
                payload = urlsafe_b64encode(f"{title}|{link}|dl|{mb*1024*1024 if mb > 0 else 0}|{password}|{imdb_id}".encode("utf-8")).decode("utf-8")
                jd_link = f"{shared_state.values['internal_address']}/download/?payload={payload}"
                
                formatted_title = title

                
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
                    debug(f"[DL-FEED-TITLE] Verbessert: '{title}' â†’ '{formatted_title}'")
                    debug(f"[DL-FEED-TITLE] Details: series='{series_part}' â†’ '{spaced_series}', season='{season_part}', rest='{rest_of_title}'")
                else:
                    # Fallback: Versuche auch andere Patterns zu erkennen
                    if re.match(r'[A-Z][a-z]+[A-Z]', title):
                        formatted_title = re.sub(r'([a-z])([A-Z])', r'\1 \2', title)
                        debug(f"[DL-FEED-TITLE] Fallback-Verbesserung: '{title}' â†’ '{formatted_title}'")
                    else:
                        debug(f"[DL-FEED-TITLE] Keine Verbesserung möglich für: '{title}'")
                
                releases.append({
                    "details": {
                        "title": formatted_title,
                        "hostname": "dl",
                        "imdb_id": imdb_id if imdb_id else "",
                        "link": jd_link,  # JDownloader-Link (für Downloads)
                        "size": int(mb * 1024 * 1024) if mb > 0 else 0,  # in Bytes
                        "date": published,
                        "source": link  # Original Thread-URL (für Sonarr-Clicks)
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


