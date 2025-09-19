#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Korrigierte Parser-Logik für data-load.me

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
        import html
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
        import re
        size_match = re.search(r'Size:\s*(\d+(?:\.\d+)?)\s*([KMG]?B)', snippet_text, re.IGNORECASE)
        if size_match:
            size_text = f"{size_match.group(1)} {size_match.group(2)}"
    
    # METHODE 2: Allgemeine Suche nach Größenmustern im gesamten Element
    if not size_text:
        all_text = result.get_text()
        import re
        size_match = re.search(r'(\d+(?:\.\d+)?)\s*([KMG]?B)', all_text, re.IGNORECASE)
        if size_match:
            size_text = f"{size_match.group(1)} {size_match.group(2)}"
    
    return size_text

def extract_date_from_result(result):
    """
    Extrahiert Datumsinformationen aus einem Suchergebnis-Element
    """
    date_text = None
    
    # METHODE 1: Suche nach time-Element mit datetime-Attribut
    time_elem = result.find('time', class_='u-dt')
    if time_elem:
        date_text = time_elem.get('datetime') or time_elem.text.strip()
    
    # METHODE 2: Suche in contentRow-minor
    if not date_text:
        minor_elem = result.find('div', class_='contentRow-minor')
        if minor_elem:
            time_elem = minor_elem.find('time')
            if time_elem:
                date_text = time_elem.get('datetime') or time_elem.text.strip()
    
    # METHODE 3: Suche nach structItem-Datums-Elementen
    if not date_text:
        struct_date = result.find('time', class_='structItem-latestDate')
        if struct_date:
            date_text = struct_date.get('datetime') or struct_date.text.strip()
    
    return date_text

# Beispiel-Integration in die bestehende dl_feed Funktion:
def corrected_dl_feed_parsing(soup, shared_state, dl, password):
    """
    Korrigierte Parsing-Logik für dl_feed
    """
    releases = []
    
    # Extrahiere Ergebnisse mit der neuen Logik
    results = extract_results_from_soup(soup)
    
    # Verarbeite jedes Ergebnis
    for result in results[:30]:  # Begrenze auf 30 Ergebnisse
        try:
            # Titel und Link extrahieren
            title, link = extract_title_and_link_from_result(result)
            
            if not title or not link:
                continue
            
            # Relativen Link zu absolutem konvertieren
            if not link.startswith(('http://', 'https://')):
                from urllib.parse import urljoin
                link = urljoin(f"https://{dl}", link)
            
            # Größe extrahieren
            size_text = extract_size_from_result(result)
            size_item = extract_size(size_text)  # Bestehende Funktion
            mb = shared_state.convert_to_mb(size_item)
            
            # Datum extrahieren
            date_text = extract_date_from_result(result)
            published = convert_to_rss_date(date_text)  # Bestehende Funktion
            
            # IMDB ID ist in diesem Kontext nicht verfügbar
            imdb_id = None
            
            # JDownloader-Link erstellen
            from base64 import urlsafe_b64encode
            source = f"https://{dl}/"
            payload = urlsafe_b64encode(f"{title}|{link}|{mb*1024*1024}|{password}|{imdb_id}".encode("utf-8")).decode("utf-8")
            jd_link = f"{shared_state.values['internal_address']}/download/?payload={payload}"
            
            releases.append({
                "details": {
                    "title": f"[DL] {title}",
                    "imdb_id": imdb_id,
                    "link": jd_link,
                    "size": mb * 1024 * 1024,  # in Bytes
                    "date": published,
                    "source": source
                },
                "type": "protected"
            })
            
        except Exception as e:
            debug(f"Fehler beim Parsen eines Ergebnisses: {e}")
            continue
    
    return releases

if __name__ == "__main__":
    print("Diese Datei enthält die korrigierte Parser-Logik für data-load.me")
    print("Sie kann verwendet werden, um die bestehende dl.py Datei zu aktualisieren.") 