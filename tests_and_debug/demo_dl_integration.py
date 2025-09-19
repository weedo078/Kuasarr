#!/usr/bin/env python3
"""
Demo-Skript für die data-load.me Integration in Quasarr

Zeigt den vollständigen Workflow:
1. Suche nach Content
2. Extrahieren von FileCrypt Links (mit Login)
3. Bereitstellung für Download-Clients
"""

import sys
import os
import requests
from bs4 import BeautifulSoup
from dataclasses import dataclass
from typing import List, Optional
import re
import time

# Setze Umgebungsvariablen für Test
os.environ['DL_USER'] = 'weedo078'
os.environ['DL_PASSWORD'] = 'zo-2!.ak'

@dataclass
class SearchResult:
    title: str
    url: str
    size: str
    site: str
    quality: str = ""
    language: str = ""
    uploader: str = ""

def create_dl_session() -> Optional[requests.Session]:
    """Erstellt eine authentifizierte Session für data-load.me"""
    
    user = os.environ.get('DL_USER')
    password = os.environ.get('DL_PASSWORD')
    dl_hostname = "data-load.me"
    
    if not user or not password:
        print("   ❌ Zugangsdaten fehlen")
        return None
    
    print(f"   🔄 Logge ein als: {user}")
    
    # Komplett neue Session erstellen
    session = requests.Session()
    
    # Browser-ähnliche Headers
    browser_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
    }
    session.headers.update(browser_headers)
    
    try:
        # SCHRITT 1: Besuche die Startseite für anfängliche Cookies
        print(f"   🔄 Besuche Startseite...")
        response = session.get(f"https://{dl_hostname}", timeout=15)
        response.raise_for_status()
        
        # SCHRITT 2: Besuche die Login-Seite
        print(f"   🔄 Lade Login-Seite...")
        login_page = session.get(f"https://{dl_hostname}/login/", timeout=15)
        login_page.raise_for_status()
        
        # HTML der Login-Seite parsen
        soup = BeautifulSoup(login_page.text, "html.parser")
        
        # SCHRITT 3: Finde das korrekte Login-Formular
        login_form = None
        
        # Suche spezifisch nach der Form mit Action "/login/login"
        for form in soup.find_all("form"):
            action = form.get("action", "")
            if "/login/login" in action or action == "/login/login":
                login_form = form
                break
        
        # Fallback: Suche nach Form mit Login-Feldern
        if not login_form:
            for form in soup.find_all("form"):
                if (form.find("input", {"name": "login"}) and 
                    form.find("input", {"type": "password"})):
                    login_form = form
                    break
        
        if not login_form:
            print("   ❌ Konnte kein Login-Formular finden")
            return None
        
        # SCHRITT 4: Extrahiere das Login-Formular und Token
        form_action = login_form.get("action", "/login/login")
        if form_action.startswith("/"):
            login_url = f"https://{dl_hostname}{form_action}"
        else:
            login_url = f"https://{dl_hostname}/{form_action}"
        
        # Sammle alle Formularfelder
        login_data = {}
        for input_field in login_form.find_all("input"):
            name = input_field.get("name")
            if not name:
                continue
                
            input_type = input_field.get("type", "text")
            value = input_field.get("value", "")
            
            # Setze Standardwerte für wichtige Felder
            if input_type == "checkbox" and name in ["remember"]:
                value = "1"
            
            login_data[name] = value
        
        # SCHRITT 5: Füge Benutzerdaten hinzu
        login_data["login"] = user
        login_data["password"] = password
        
        # SCHRITT 6: Sende Login-Request
        print(f"   🔄 Sende Login-Daten...")
        
        # Verbesserte Headers für Login-Request
        login_headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': f'https://{dl_hostname}',
            'Referer': f'https://{dl_hostname}/login/',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
        }
        
        session.headers.update(login_headers)
        
        login_response = session.post(login_url, data=login_data, timeout=15, allow_redirects=True)
        
        print(f"   📍 Login Response Status: {login_response.status_code}")
        print(f"   📍 Login Response URL: {login_response.url}")
        
        # SCHRITT 7: Prüfe, ob der Login erfolgreich war
        login_success = False
        
        # Mehrere Methoden zur Validierung
        response_text = login_response.text.lower()
        
        # Check 1: URL enthält nicht mehr "login"
        if "login" not in login_response.url:
            login_success = True
            print("   ✅ Login erfolgreich (URL-Check)")
        
        # Check 2: Suche nach Logout-Links
        elif any(keyword in response_text for keyword in ["logout", "abmelden", "sign out"]):
            login_success = True
            print("   ✅ Login erfolgreich (Logout-Link gefunden)")
        
        # Check 3: Suche nach Dashboard/Profile-Indikatoren
        elif any(keyword in response_text for keyword in ["dashboard", "profile", "account", "konto"]):
            login_success = True
            print("   ✅ Login erfolgreich (Dashboard gefunden)")
        
        # Check 4: Keine Fehlermeldungen
        elif not any(keyword in response_text for keyword in ["error", "fehler", "invalid", "ungültig", "wrong", "falsch"]):
            # Zusätzlicher Test: Versuche eine geschützte Seite zu laden
            test_response = session.get(f"https://{dl_hostname}/", timeout=10)
            if test_response.status_code == 200:
                test_text = test_response.text.lower()
                if any(keyword in test_text for keyword in ["logout", "abmelden", "profile", "dashboard"]):
                    login_success = True
                    print("   ✅ Login erfolgreich (Bestätigung durch geschützte Seite)")
        
        if login_success:
            print(f"   ✅ Login erfolgreich für {user}")
            return session
        else:
            print(f"   ❌ Login fehlgeschlagen für {user}")
            print(f"   📍 Response enthielt: {response_text[:200]}...")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Netzwerkfehler beim Login: {e}")
        return None
    except Exception as e:
        print(f"   ❌ Unerwarteter Fehler beim Login: {e}")
        return None

def dl_search_simple(query: str) -> List[SearchResult]:
    """Vereinfachte dl_search Funktion für Demo"""
    
    print(f"   🔄 Authentifiziere bei data-load.me...")
    
    session = create_dl_session()
    if not session:
        return []
    
    # Suche mit korrekter Formular-Simulation
    print(f"   🔄 Suche nach '{query}'...")
    dl_hostname = "data-load.me"
    
    try:
        # SCHRITT 1: Lade die Such-Seite mit dem Suchbegriff
        initial_search_url = f"https://{dl_hostname}/search/?q={query}"
        print(f"   📄 Lade Such-Seite: {initial_search_url}")
        
        search_page = session.get(initial_search_url, timeout=15)
        
        if search_page.status_code != 200:
            print(f"   ❌ Fehler beim Laden der Such-Seite: {search_page.status_code}")
            return []
        
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
            print("   ❌ Kein Such-Formular gefunden")
            return []
        
        # SCHRITT 3: Sammle Formular-Daten
        form_action = search_form.get('action', '/search/search')
        if not form_action.startswith('http'):
            search_url = f"https://{dl_hostname}{form_action}"
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
                value = query
            elif input_type == 'checkbox':
                value = ''  # Checkboxen nicht aktiviert
            
            form_data[name] = value
        
        # SCHRITT 4: Sende Such-Request (verwende GET da POST fehlschlägt)
        print(f"   🔄 Führe Suche aus...")
        
        # Konvertiere form_data zu URL-Parametern (nur nicht-leere Werte)
        get_params = {}
        for key, value in form_data.items():
            if value:
                get_params[key] = value
        
        search_response = session.get(search_url, params=get_params, timeout=15, allow_redirects=True)
        
        if search_response.status_code != 200:
            print(f"   ❌ Such-Request fehlgeschlagen: {search_response.status_code}")
            return []
        
        print(f"   ✅ Suchergebnisse geladen: {search_response.url}")
        
        # SCHRITT 5: Parse Suchergebnisse
        soup = BeautifulSoup(search_response.text, 'html.parser')
        results = []
        
        # Methode 1: XenForo structItem (modern)
        struct_items = soup.find_all('div', class_='structItem')
        
        for item in struct_items[:10]:  # Maximal 10 Ergebnisse
            try:
                # Titel-Element suchen
                title_elem = item.find('div', class_='structItem-title')
                if title_elem:
                    link = title_elem.find('a')
                    if link:
                        title_text = link.get_text(strip=True)
                        href = link.get('href', '')
                        
                        if not href.startswith('http'):
                            href = f"https://{dl_hostname}{href}"
                        
                        # Zusätzliche Infos
                        snippet = item.find('div', class_='structItem-snippet')
                        snippet_text = snippet.get_text(strip=True) if snippet else ""
                        
                        # Größe aus Snippet extrahieren
                        size_text = "Unbekannt"
                        size_match = re.search(r'(\d+(?:\.\d+)?)\s*([KMG]?B)', snippet_text, re.IGNORECASE)
                        if size_match:
                            size_text = f"{size_match.group(1)} {size_match.group(2)}"
                        
                        results.append(SearchResult(
                            title=title_text,
                            url=href,
                            size=size_text,
                            site="data-load.me"
                        ))
                        
            except Exception as e:
                print(f"   ⚠️ Fehler beim Parsen: {e}")
                continue
        
        # Methode 2: Fallback für Links mit 'thread' oder 'topic'
        if not results:
            print("   📄 Fallback: Parse allgemeine Links...")
            all_links = soup.find_all('a', href=True)
            for link in all_links:
                href = link.get('href', '')
                text = link.get_text(strip=True)
                
                if (('thread' in href.lower() or 'topic' in href.lower()) and 
                    text and len(text) > 10 and query.lower() in text.lower()):
                    
                    if not href.startswith('http'):
                        href = f"https://{dl_hostname}{href}"
                    
                    results.append(SearchResult(
                        title=text,
                        url=href,
                        size="Unbekannt",
                        site="data-load.me"
                    ))
        
        print(f"   ✅ {len(results)} Suchergebnisse verarbeitet")
        return results
        
    except Exception as e:
        print(f"   ❌ Allgemeiner Such-Fehler: {e}")
        return []

def get_filecrypt_links_simple(topic_url: str) -> List[str]:
    """Vereinfachte get_filecrypt_links Funktion für Demo"""
    
    print(f"   🔄 Lade Topic-Seite...")
    
    session = create_dl_session()
    if not session:
        return []
    
    try:
        # Topic-Seite laden
        topic_response = session.get(topic_url, timeout=15)
        
        if topic_response.status_code != 200:
            print(f"   ❌ Topic nicht erreichbar (Status: {topic_response.status_code})")
            return []
        
        soup = BeautifulSoup(topic_response.content, 'html.parser')
        
        # Suche nach FileCrypt Links
        filecrypt_links = []
        
        # Verschiedene Patterns für FileCrypt Links
        patterns = [
            r'https?://filecrypt\.(?:cc|co)/[^\s<>"\']+',
            r'filecrypt\.(?:cc|co)/[^\s<>"\']+',
        ]
        
        text_content = soup.get_text()
        
        for pattern in patterns:
            matches = re.findall(pattern, text_content, re.IGNORECASE)
            for match in matches:
                if not match.startswith('http'):
                    match = f"https://{match}"
                if match not in filecrypt_links:
                    filecrypt_links.append(match)
        
        # Auch in href-Attributen suchen
        for link in soup.find_all('a', href=True):
            href = link['href']
            if 'filecrypt' in href.lower():
                if not href.startswith('http'):
                    href = f"https://{href}"
                if href not in filecrypt_links:
                    filecrypt_links.append(href)
        
        print(f"   ✅ {len(filecrypt_links)} FileCrypt-Links gefunden")
        return filecrypt_links[:10]  # Maximal 10 Links
        
    except Exception as e:
        print(f"   ❌ Fehler beim Laden der Topic-Seite: {e}")
        return []

def demo():
    print("=== data-load.me Integration Demo ===\n")
    
    # Suchbegriffe definieren
    search_terms = [
        "Matrix",
        "The Last of Us s02", 
        "rick and morty s03",
        "the conjuring"
    ]
    
    print(f"Teste {len(search_terms)} verschiedene Suchbegriffe...\n")
    
    for i, search_term in enumerate(search_terms, 1):
        print(f"{'='*60}")
        print(f"SUCHE {i}: '{search_term}'")
        print(f"{'='*60}")
        
        # Suche nach Content
        print(f"🔍 Suche nach '{search_term}'...")
        search_results = dl_search_simple(search_term)
        
        if not search_results:
            print("   ❌ Keine Ergebnisse gefunden!\n")
            continue
            
        print(f"   ✅ {len(search_results)} Ergebnisse gefunden!\n")
        
        # Zeige die ersten 3 Treffer (falls vorhanden)
        max_results = min(3, len(search_results))
        
        for j in range(max_results):
            result = search_results[j]
            print(f"📋 TREFFER {j+1}:")
            print(f"   📝 Titel: {result.title}")
            print(f"   🔗 Forum-Link: {result.url}")
            print(f"   📦 Größe: {result.size}")
            print(f"   🌐 Hoster: {result.site}")
            
            # Hole FileCrypt Download-Links
            print(f"   📥 Extrahiere Download-Links...")
            filecrypt_links = get_filecrypt_links_simple(result.url)
            
            if filecrypt_links:
                print(f"   ✅ {len(filecrypt_links)} Download-Links gefunden:")
                for k, link in enumerate(filecrypt_links, 1):
                    print(f"      {k}. {link}")
            else:
                print("   ❌ Keine Download-Links verfügbar")
            
            print()  # Leerzeile zwischen Treffern
        
        if len(search_results) > 3:
            print(f"   ... und {len(search_results) - 3} weitere Treffer\n")
    
    print(f"{'='*60}")
    print("=== DEMO ABGESCHLOSSEN ===")
    print(f"{'='*60}")
    print("\n💡 Hinweise:")
    print("- FileCrypt Links sind nur nach Login sichtbar")
    print("- Links enthalten verschlüsselte Container")
    print("- JDownloader kann diese automatisch entschlüsseln")
    print(f"- Eingeloggt als: {os.environ.get('DL_USER')}")

if __name__ == "__main__":
    demo() 