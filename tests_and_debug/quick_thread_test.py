#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Schneller Test für Thread-Analyse

import requests
from bs4 import BeautifulSoup
import re

def test_thread_quick():
    """Schneller Test der Thread-Seite"""
    
    print("[*] === SCHNELLER THREAD-TEST ===")
    
    # Setup
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36'
    }
    
    session = requests.Session()
    session.headers.update(headers)
    
    # Teste die bekannte Thread-URL
    thread_url = "https://www.data-load.me/threads/the-last-of-us-s02-german-aac-1080p-web-x265-w00t.921932/"
    
    try:
        print(f"[+] Lade Thread: {thread_url}")
        
        response = session.get(thread_url, timeout=10)
        response.raise_for_status()
        
        print(f"[+] Thread geladen (Status: {response.status_code})")
        
        # Speichere HTML für weitere Analyse
        with open('thread_content.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Suche nach FileCrypt-Links in verschiedenen Formen
        filecrypt_links = []
        
        # 1. Direkte Links
        all_links = soup.find_all('a', href=True)
        for link in all_links:
            href = link.get('href', '')
            if 'filecrypt.cc' in href or 'filecrypt.co' in href:
                filecrypt_links.append(href)
                print(f"[+] Direkter FileCrypt-Link: {href}")
        
        # 2. Text-basierte Suche
        text_content = response.text
        
        # Verschiedene FileCrypt-Pattern
        patterns = [
            r'https?://(?:www\.)?filecrypt\.cc/[^\s\<\>\"\']+',
            r'https?://(?:www\.)?filecrypt\.co/[^\s\<\>\"\']+',
            r'filecrypt\.cc/[^\s\<\>\"\']+',
            r'filecrypt\.co/[^\s\<\>\"\']+',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text_content, re.IGNORECASE)
            for match in matches:
                if not match.startswith('http'):
                    match = 'https://' + match
                if match not in filecrypt_links:
                    filecrypt_links.append(match)
                    print(f"[+] Text-FileCrypt-Link: {match}")
        
        # 3. Schaue nach versteckten/kodierten Links
        # Manchmal sind Links in JavaScript oder Base64 kodiert
        
        # Suche nach "Container" URLs (typisch für FileCrypt)
        container_pattern = r'Container/[A-F0-9]+\.html'
        containers = re.findall(container_pattern, text_content, re.IGNORECASE)
        
        for container in containers:
            full_url = f"https://filecrypt.cc/{container}"
            if full_url not in filecrypt_links:
                filecrypt_links.append(full_url)
                print(f"[+] Container-FileCrypt-Link: {full_url}")
        
        # 4. Suche nach anderen Download-Links
        other_hosts = []
        host_patterns = [
            (r'https?://(?:www\.)?rapidgator\.net/[^\s\<\>\"\']+', 'RapidGator'),
            (r'https?://(?:www\.)?turbobit\.net/[^\s\<\>\"\']+', 'TurboBit'),
            (r'https?://(?:www\.)?nitroflare\.com/[^\s\<\>\"\']+', 'NitroFlare'),
            (r'https?://(?:www\.)?uploaded\.net/[^\s\<\>\"\']+', 'Uploaded'),
            (r'https?://(?:www\.)?mixdrop\.co/[^\s\<\>\"\']+', 'MixDrop'),
        ]
        
        for pattern, host_name in host_patterns:
            matches = re.findall(pattern, text_content, re.IGNORECASE)
            for match in matches:
                other_hosts.append((host_name, match))
                print(f"[+] {host_name}-Link: {match}")
        
        # Ergebnisse
        print(f"\n[+] ZUSAMMENFASSUNG:")
        print(f"[+] {len(filecrypt_links)} FileCrypt-Links gefunden")
        print(f"[+] {len(other_hosts)} andere Host-Links gefunden")
        
        if filecrypt_links:
            print(f"\n[*] FileCrypt-Links:")
            for i, link in enumerate(filecrypt_links, 1):
                print(f"  {i}. {link}")
        
        if other_hosts:
            print(f"\n[*] Andere Download-Links:")
            for i, (host, link) in enumerate(other_hosts, 1):
                print(f"  {i}. [{host}] {link}")
        
        # Schaue nach der Release-Information
        print(f"\n[*] Release-Informationen suchen...")
        
        # Suche nach typischen Release-Info-Mustern
        title_elem = soup.find('title')
        if title_elem:
            print(f"[+] Seitentitel: {title_elem.text.strip()}")
        
        # Suche nach ersten Post/Artikel
        article = soup.find('article')
        if article:
            article_text = article.get_text()[:500]
            print(f"[+] Artikel-Beginn: {article_text}")
        
        return filecrypt_links
        
    except Exception as e:
        print(f"[-] Fehler: {e}")
        return []

if __name__ == "__main__":
    filecrypt_links = test_thread_quick()
    
    if filecrypt_links:
        print(f"\n[✓] Test erfolgreich! {len(filecrypt_links)} FileCrypt-Links extrahiert.")
    else:
        print(f"\n[!] Keine FileCrypt-Links gefunden oder Fehler aufgetreten.") 