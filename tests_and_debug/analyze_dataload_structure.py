#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Analyse-Script für data-load.me HTML-Strukturen

import requests
from bs4 import BeautifulSoup
import re
import time
import random
import argparse
import json
import os
from urllib.parse import urljoin, urlparse, parse_qs

# User-Agent für legitimere Anfragen
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36"

# Basis-URL (kann angepasst werden)
BASE_URL = "https://www.data-load.me"

def setup_session():
    """Eine Session mit Browser-ähnlichen Headers einrichten"""
    session = requests.Session()
    session.headers.update({
        'User-Agent': USER_AGENT,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    })
    return session

def login_to_dataload(session, username, password):
    """Login bei data-load.me durchführen"""
    print(f"[*] Versuche Login bei {BASE_URL}...")
    
    try:
        # Schritt 1: Startseite besuchen
        print("[*] Besuche Startseite...")
        response = session.get(BASE_URL, timeout=10)
        response.raise_for_status()
        print(f"[+] Startseite geladen (Status: {response.status_code})")
        
        # Schritt 2: Login-Seite besuchen
        login_url = f"{BASE_URL}/login/"
        print(f"[*] Besuche Login-Seite: {login_url}")
        login_page = session.get(login_url, timeout=10)
        login_page.raise_for_status()
        
        # HTML der Login-Seite parsen
        soup = BeautifulSoup(login_page.text, "html.parser")
        
        # Schritt 3: Login-Formular finden
        login_form = soup.find("form", {"action": re.compile(r"/login/")})
        if not login_form:
            # Alternativ: jedes Formular mit Passwort-Feld
            for form in soup.find_all("form"):
                if form.find("input", {"type": "password"}):
                    login_form = form
                    break
        
        if not login_form:
            print("[-] Konnte kein Login-Formular finden")
            return False
        
        print("[+] Login-Formular gefunden")
        
        # Schritt 4: Formular-Action und Felder extrahieren
        form_action = login_form.get("action", "/login/login")
        if form_action.startswith("/"):
            post_url = f"{BASE_URL}{form_action}"
        else:
            post_url = f"{BASE_URL}/{form_action}"
        
        print(f"[*] Login-URL: {post_url}")
        
        # Alle Formularfelder sammeln
        login_data = {}
        for input_field in login_form.find_all("input"):
            name = input_field.get("name")
            if not name:
                continue
            
            value = input_field.get("value", "")
            login_data[name] = value
            
            # Debug-Ausgabe (außer Passwort)
            if input_field.get("type") != "password":
                print(f"[*] Formularfeld: {name}={value}")
        
        # Benutzerdaten hinzufügen
        login_data["login"] = username
        login_data["password"] = password
        login_data["remember"] = "1"  # Remember me
        
        # Schritt 5: Login-Request senden
        session.headers.update({
            "Referer": login_url,
            "Origin": BASE_URL,
            "Content-Type": "application/x-www-form-urlencoded"
        })
        
        print("[*] Sende Login-Request...")
        login_response = session.post(post_url, data=login_data, timeout=10, allow_redirects=True)
        print(f"[*] Login-Response-Status: {login_response.status_code}")
        print(f"[*] Login-Response-URL: {login_response.url}")
        
        # Schritt 6: Login-Erfolg prüfen
        home_page = session.get(BASE_URL, timeout=10)
        
        # Prüfe auf Logout-Link oder ähnliches
        is_logged_in = ("logout" in home_page.text.lower() or 
                       "abmelden" in home_page.text.lower() or
                       "account" in home_page.text.lower())
        
        if is_logged_in:
            print("[+] Login erfolgreich!")
            return True
        else:
            print("[-] Login fehlgeschlagen")
            return False
            
    except Exception as e:
        print(f"[-] Fehler beim Login: {e}")
        return False

def extract_search_id(session):
    """Such-ID aus der Hauptseite extrahieren"""
    try:
        response = session.get(BASE_URL, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Suche nach Formularen mit /search/ Action
        search_forms = soup.find_all('form', action=re.compile(r'/search/'))
        if search_forms:
            action_url = search_forms[0].get('action', '')
            search_id_match = re.search(r'/search/(\d+)/', action_url)
            if search_id_match:
                search_id = search_id_match.group(1)
                print(f"[+] Such-ID aus Formular extrahiert: {search_id}")
                return search_id
        
        # Suche nach Links mit /search/ID/ Muster
        search_links = soup.find_all('a', href=re.compile(r'/search/\d+/'))
        if search_links:
            href = search_links[0].get('href', '')
            search_id_match = re.search(r'/search/(\d+)/', href)
            if search_id_match:
                search_id = search_id_match.group(1)
                print(f"[+] Such-ID aus Link extrahiert: {search_id}")
                return search_id
        
        # Fallback
        search_id = "34811168"
        print(f"[!] Keine Such-ID gefunden, verwende Fallback: {search_id}")
        return search_id
        
    except Exception as e:
        print(f"[-] Fehler beim Extrahieren der Such-ID: {e}")
        return "34811168"

def analyze_search_page(session, search_id, query="test"):
    """Analysiere eine Suchseite und deren Struktur"""
    print(f"\n[*] Analysiere Suchseite für Query: '{query}'")
    
    try:
        # Suchparameter
        params = {
            'q': query,
            'c[title_only]': 1,
            'o': 'relevance'
        }
        
        search_url = f"{BASE_URL}/search/{search_id}/"
        print(f"[*] Such-URL: {search_url}")
        print(f"[*] Parameter: {params}")
        
        # Kleine Verzögerung
        time.sleep(random.uniform(1, 2))
        
        # Anfrage senden
        response = session.get(search_url, params=params, timeout=10)
        response.raise_for_status()
        
        print(f"[+] Suchseite geladen (Status: {response.status_code})")
        print(f"[+] Finale URL: {response.url}")
        
        # HTML speichern für Analyse
        filename = f"dataload_search_{query.replace(' ', '_')}.html"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(response.text)
        print(f"[+] HTML gespeichert in: {filename}")
        
        # Grundlegende Analyse
        soup = BeautifulSoup(response.text, 'html.parser')
        
        print(f"\n[*] Seitentitel: {soup.find('title').text if soup.find('title') else 'Nicht gefunden'}")
        
        # Suche nach verschiedenen Strukturen
        analyze_page_structure(soup, "Suchseite")
        
        return response.text
        
    except Exception as e:
        print(f"[-] Fehler beim Analysieren der Suchseite: {e}")
        return None

def analyze_feed_page(session, search_id):
    """Analysiere die Feed-Seite (neueste Releases)"""
    print(f"\n[*] Analysiere Feed-Seite (neueste Releases)")
    
    try:
        # Feed-URL (sortiert nach Datum)
        feed_url = f"{BASE_URL}/search/{search_id}/?o=date"
        print(f"[*] Feed-URL: {feed_url}")
        
        # Kleine Verzögerung
        time.sleep(random.uniform(1, 2))
        
        # Anfrage senden
        response = session.get(feed_url, timeout=10)
        response.raise_for_status()
        
        print(f"[+] Feed-Seite geladen (Status: {response.status_code})")
        
        # HTML speichern
        filename = "dataload_feed.html"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(response.text)
        print(f"[+] HTML gespeichert in: {filename}")
        
        # Analyse
        soup = BeautifulSoup(response.text, 'html.parser')
        analyze_page_structure(soup, "Feed-Seite")
        
        return response.text
        
    except Exception as e:
        print(f"[-] Fehler beim Analysieren der Feed-Seite: {e}")
        return None

def analyze_page_structure(soup, page_type):
    """Analysiere die HTML-Struktur einer Seite"""
    print(f"\n[*] === STRUKTURANALYSE: {page_type} ===")
    
    # 1. Suche nach möglichen Thread/Diskussions-Containern
    discussion_items = soup.find_all(['li', 'div'], class_=re.compile(r'(discussion|thread|item)', re.I))
    print(f"[*] Gefundene Diskussions-Container: {len(discussion_items)}")
    
    if discussion_items:
        for i, item in enumerate(discussion_items[:3]):  # Nur erste 3 anzeigen
            print(f"  [{i+1}] Tag: {item.name}, Klassen: {item.get('class', [])}")
            # Suche nach Titel-Links
            title_links = item.find_all('a')
            for link in title_links[:2]:  # Erste 2 Links
                print(f"       Link: {link.text.strip()[:50]}... -> {link.get('href', 'Kein href')}")
    
    # 2. Suche nach H-Tags mit Links
    h_tags = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5'])
    relevant_h_tags = [h for h in h_tags if h.find('a')]
    print(f"[*] H-Tags mit Links: {len(relevant_h_tags)}")
    
    if relevant_h_tags:
        for i, h_tag in enumerate(relevant_h_tags[:3]):
            link = h_tag.find('a')
            print(f"  [{i+1}] {h_tag.name}: {link.text.strip()[:50]}... -> {link.get('href', 'Kein href')}")
    
    # 3. Suche nach Titel-Klassen
    title_elements = soup.find_all(class_=re.compile(r'title', re.I))
    print(f"[*] Elemente mit 'title' in der Klasse: {len(title_elements)}")
    
    if title_elements:
        for i, elem in enumerate(title_elements[:3]):
            text = elem.get_text(strip=True)[:50]
            print(f"  [{i+1}] {elem.name}: {text}...")
    
    # 4. Suche nach Größenangaben
    size_patterns = soup.find_all(text=re.compile(r'\d+\s*[KMG]?B', re.I))
    print(f"[*] Gefundene Größenangaben: {len(size_patterns)}")
    
    for i, size_text in enumerate(size_patterns[:5]):
        print(f"  [{i+1}] {size_text.strip()}")
    
    # 5. Suche nach Datum-Elementen
    date_elements = soup.find_all(class_=re.compile(r'date|time', re.I))
    print(f"[*] Elemente mit Datum/Zeit-Klassen: {len(date_elements)}")
    
    for i, elem in enumerate(date_elements[:3]):
        print(f"  [{i+1}] {elem.name}: {elem.get_text(strip=True)}")

def analyze_thread_page(session, thread_url):
    """Analysiere eine spezifische Thread-Seite auf FileCrypt-Links"""
    print(f"\n[*] Analysiere Thread-Seite: {thread_url}")
    
    try:
        # Relative URL zu absolute konvertieren
        if not thread_url.startswith(('http://', 'https://')):
            thread_url = urljoin(BASE_URL, thread_url)
        
        print(f"[*] Vollständige URL: {thread_url}")
        
        # Kleine Verzögerung
        time.sleep(random.uniform(1, 2))
        
        # Anfrage senden
        response = session.get(thread_url, timeout=10)
        response.raise_for_status()
        
        print(f"[+] Thread-Seite geladen (Status: {response.status_code})")
        
        # HTML speichern
        filename = f"dataload_thread_{int(time.time())}.html"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(response.text)
        print(f"[+] HTML gespeichert in: {filename}")
        
        # Nach FileCrypt-Links suchen
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Suche nach FileCrypt-Links
        filecrypt_links = []
        
        # Methode 1: Direkte Links zu filecrypt.cc
        direct_links = soup.find_all('a', href=re.compile(r'filecrypt\.cc', re.I))
        filecrypt_links.extend([link.get('href') for link in direct_links])
        
        # Methode 2: Links im Text
        text_links = soup.find_all(text=re.compile(r'filecrypt\.cc', re.I))
        for text in text_links:
            # Versuche URL aus Text zu extrahieren
            urls = re.findall(r'https?://[^\s]+filecrypt\.cc[^\s]*', str(text))
            filecrypt_links.extend(urls)
        
        print(f"[+] Gefundene FileCrypt-Links: {len(filecrypt_links)}")
        
        for i, link in enumerate(filecrypt_links):
            print(f"  [{i+1}] {link}")
        
        # Allgemeine Struktur-Analyse
        analyze_page_structure(soup, "Thread-Seite")
        
        return filecrypt_links
        
    except Exception as e:
        print(f"[-] Fehler beim Analysieren der Thread-Seite: {e}")
        return []

def main():
    parser = argparse.ArgumentParser(description='Analysiere data-load.me HTML-Strukturen')
    parser.add_argument('--username', '-u', help='Benutzername für data-load.me')
    parser.add_argument('--password', '-p', help='Passwort für data-load.me')
    parser.add_argument('--search', '-s', default='test', help='Suchbegriff für Tests')
    parser.add_argument('--thread-url', '-t', help='Spezifische Thread-URL zum Analysieren')
    parser.add_argument('--no-login', action='store_true', help='Versuche ohne Login (falls möglich)')
    
    args = parser.parse_args()
    
    # Login-Daten aus Umgebungsvariablen, falls nicht als Argument übergeben
    username = args.username or os.getenv('DL_USERNAME')
    password = args.password or os.getenv('DL_PASSWORD')
    
    if not args.no_login and (not username or not password):
        print("[-] Benutzername und Passwort erforderlich!")
        print("    Verwende: --username <user> --password <pass>")
        print("    Oder setze Umgebungsvariablen: DL_USERNAME, DL_PASSWORD")
        print("    Oder verwende --no-login für Versuche ohne Anmeldung")
        return
    
    print("[*] Starte data-load.me Struktur-Analyse...")
    
    # Session einrichten
    session = setup_session()
    
    # Login (falls nicht übersprungen)
    if not args.no_login:
        if not login_to_dataload(session, username, password):
            print("[-] Login fehlgeschlagen, breche ab")
            return
    else:
        print("[!] Überspringe Login-Prozess")
    
    # Such-ID extrahieren
    search_id = extract_search_id(session)
    
    # Feed-Seite analysieren
    analyze_feed_page(session, search_id)
    
    # Suchseite analysieren
    analyze_search_page(session, search_id, args.search)
    
    # Spezifische Thread-URL analysieren (falls angegeben)
    if args.thread_url:
        analyze_thread_page(session, args.thread_url)
    
    print("\n[+] Analyse abgeschlossen!")
    print("[*] HTML-Dateien wurden zur weiteren Untersuchung gespeichert")

if __name__ == "__main__":
    main() 