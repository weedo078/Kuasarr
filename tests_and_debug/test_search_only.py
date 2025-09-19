#!/usr/bin/env python3
"""
Test der Suchfunktion mit Formular-Simulation
"""

import requests
from bs4 import BeautifulSoup
import re

def test_search_with_form():
    print("=== TEST MIT SUCH-FORMULAR SIMULATION ===\n")
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    
    search_term = "Matrix"
    
    try:
        # SCHRITT 1: Lade die Such-Seite mit dem Suchbegriff
        initial_search_url = f"https://data-load.me/search/?q={search_term}"
        print(f"🔍 1. Lade Such-Seite: {initial_search_url}")
        
        search_page = session.get(initial_search_url, timeout=15)
        print(f"   Status: {search_page.status_code}")
        print(f"   Final URL: {search_page.url}")
        
        if search_page.status_code != 200:
            print(f"❌ Fehler beim Laden der Such-Seite: {search_page.status_code}")
            return
        
        # SCHRITT 2: Parse das Such-Formular
        soup = BeautifulSoup(search_page.text, 'html.parser')
        
        title = soup.find('title')
        if title:
            print(f"   Seitentitel: {title.get_text().strip()}")
        
        # Finde das Such-Formular
        search_form = None
        forms = soup.find_all('form')
        print(f"   Gefundene Formulare: {len(forms)}")
        
        for i, form in enumerate(forms):
            action = form.get('action', 'keine')
            print(f"   Form {i+1}: Action = {action}")
            
            # Suche nach dem Such-Formular (hat keywords input)
            if form.find('input', {'name': 'keywords'}) or '/search' in action:
                search_form = form
                print(f"   ✅ Such-Formular gefunden!")
                break
        
        if not search_form:
            print("   ❌ Kein Such-Formular gefunden")
            return
        
        # SCHRITT 3: Sammle Formular-Daten
        print("🔄 2. Bereite Such-Formular vor...")
        
        form_action = search_form.get('action', '/search/search')
        if not form_action.startswith('http'):
            search_url = f"https://data-load.me{form_action}"
        else:
            search_url = form_action
        
        print(f"   Such-URL: {search_url}")
        
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
                value = search_term
            elif input_type == 'checkbox':
                # Standard: Checkboxen nicht aktiviert (außer explizit gewünscht)
                value = ''
            
            form_data[name] = value
            print(f"   Form-Feld: {name} = '{value}' ({input_type})")
        
        # SCHRITT 4: Sende Such-Request (simuliere "Suchen" Button)
        print("🔄 3. Sende Such-Request...")
        
        # Debug: Zeige was wir senden werden
        print(f"   Formular-Daten: {form_data}")
        
        # Headers für POST-Request
        post_headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': 'https://data-load.me',
            'Referer': initial_search_url,
        }
        session.headers.update(post_headers)
        
        # Versuche zuerst POST
        search_response = session.post(search_url, data=form_data, timeout=15, allow_redirects=True)
        print(f"   POST Status: {search_response.status_code}")
        print(f"   POST Final URL: {search_response.url}")
        
        # Falls POST fehlschlägt, versuche GET mit Parametern
        if search_response.status_code != 200:
            print("   ⚠️ POST fehlgeschlagen, versuche GET...")
            
            # Konvertiere form_data zu URL-Parametern
            get_params = {}
            for key, value in form_data.items():
                if value:  # Nur nicht-leere Werte
                    get_params[key] = value
            
            search_response = session.get(search_url, params=get_params, timeout=15, allow_redirects=True)
            print(f"   GET Status: {search_response.status_code}")
            print(f"   GET Final URL: {search_response.url}")
        
        if search_response.status_code != 200:
            print(f"   ❌ Beide Methoden fehlgeschlagen")
            
            # Debug: Zeige Response-Content
            print(f"   Response Content Preview: {search_response.text[:500]}")
            return
        
        # SCHRITT 5: Parse Suchergebnisse
        print("📋 4. Parse Suchergebnisse...")
        
        soup = BeautifulSoup(search_response.text, 'html.parser')
        
        # Überprüfe, ob wir auf der Ergebnisseite sind
        page_title = soup.find('title')
        if page_title:
            print(f"   Ergebnis-Seitentitel: {page_title.get_text().strip()}")
        
        results = []
        
        # Methode 1: XenForo structItem (modern)
        struct_items = soup.find_all('div', class_='structItem')
        print(f"   Gefundene structItem Elemente: {len(struct_items)}")
        
        for item in struct_items[:10]:
            try:
                # Titel-Element suchen
                title_elem = item.find('div', class_='structItem-title')
                if title_elem:
                    link = title_elem.find('a')
                    if link:
                        title_text = link.get_text(strip=True)
                        href = link.get('href', '')
                        
                        # Zusätzliche Infos
                        snippet = item.find('div', class_='structItem-snippet')
                        snippet_text = snippet.get_text(strip=True) if snippet else ""
                        
                        # Meta-Infos (Forum, Datum, etc.)
                        meta = item.find('div', class_='structItem-meta')
                        meta_text = meta.get_text(strip=True) if meta else ""
                        
                        results.append({
                            'title': title_text,
                            'url': href,
                            'snippet': snippet_text[:150] + "..." if len(snippet_text) > 150 else snippet_text,
                            'meta': meta_text
                        })
                        
            except Exception as e:
                print(f"   ⚠️ Fehler beim Parsen eines Ergebnisses: {e}")
        
        # Methode 2: Alternative Parsing-Methoden als Fallback
        if not results:
            print("   Fallback: Suche nach Links mit 'thread' oder 'topics'...")
            all_links = soup.find_all('a', href=True)
            for link in all_links:
                href = link.get('href', '')
                text = link.get_text(strip=True)
                
                if (('thread' in href.lower() or 'topic' in href.lower()) and 
                    text and len(text) > 10):
                    results.append({
                        'title': text,
                        'url': href,
                        'snippet': "",
                        'meta': ""
                    })
        
        print(f"\n🎯 GEFUNDENE ERGEBNISSE: {len(results)}")
        
        for i, result in enumerate(results, 1):
            print(f"\n{i}. {result['title']}")
            print(f"   🔗 URL: {result['url']}")
            if result['snippet']:
                print(f"   📝 Snippet: {result['snippet']}")
            if result['meta']:
                print(f"   📊 Meta: {result['meta']}")
        
        if results:
            print("\n✅ Suchergebnisse erfolgreich gefunden!")
            
            # SCHRITT 6: Teste FileCrypt-Extraktion für ersten Treffer
            if results:
                first_result = results[0]
                first_url = first_result['url']
                if not first_url.startswith('http'):
                    first_url = f"https://data-load.me{first_url}"
                
                print(f"\n🔗 5. Teste FileCrypt-Extraktion für: {first_result['title']}")
                print(f"   URL: {first_url}")
                
                try:
                    topic_response = session.get(first_url, timeout=15)
                    if topic_response.status_code == 200:
                        topic_soup = BeautifulSoup(topic_response.text, 'html.parser')
                        
                        # Suche nach FileCrypt Links
                        filecrypt_links = []
                        text_content = topic_soup.get_text()
                        
                        patterns = [
                            r'https?://filecrypt\.(?:cc|co)/[^\s<>"\']+',
                            r'filecrypt\.(?:cc|co)/[^\s<>"\']+',
                        ]
                        
                        for pattern in patterns:
                            matches = re.findall(pattern, text_content, re.IGNORECASE)
                            for match in matches:
                                if not match.startswith('http'):
                                    match = f"https://{match}"
                                if match not in filecrypt_links:
                                    filecrypt_links.append(match)
                        
                        print(f"   📥 Gefundene FileCrypt Links: {len(filecrypt_links)}")
                        for j, link in enumerate(filecrypt_links[:5], 1):  # Zeige nur erste 5
                            print(f"   {j}. {link}")
                        
                        if len(filecrypt_links) > 5:
                            print(f"   ... und {len(filecrypt_links) - 5} weitere Links")
                    
                    else:
                        print(f"   ❌ Topic nicht erreichbar: {topic_response.status_code}")
                
                except Exception as e:
                    print(f"   ❌ Fehler beim Laden des Topics: {e}")
        
        else:
            print("\n❌ Keine Suchergebnisse gefunden")
            
            # Debug: Zeige einen Teil des HTML
            print("\nDEBUG - HTML Preview (erste 1000 Zeichen):")
            print(search_response.text[:1000])
            print("...\n")
    
    except Exception as e:
        print(f"❌ Allgemeiner Fehler: {e}")
    
    print("\n=== TEST ABGESCHLOSSEN ===")

if __name__ == "__main__":
    test_search_with_form() 