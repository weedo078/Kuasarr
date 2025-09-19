#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import requests
import json
import os
from bs4 import BeautifulSoup

def load_dl_cookies():
    """Load DL cookies from available cookie files"""
    cookie_paths = [
        "config/dl_cookies.json",
        "dl_cookies.json"
    ]
    
    for cookie_path in cookie_paths:
        if os.path.exists(cookie_path):
            try:
                with open(cookie_path, 'r') as f:
                    cookies_data = json.load(f)
                print(f"✓ Loaded cookies from {cookie_path}")
                return cookies_data
            except Exception as e:
                print(f"✗ Failed to load cookies from {cookie_path}: {e}")
                continue
    
    print("✗ No cookie file found")
    return None

def create_authenticated_session():
    """Create a session with DL cookies"""
    cookies_data = load_dl_cookies()
    if not cookies_data:
        return None
    
    session = requests.Session()
    hostname = "data-load.me"
    
    try:
        # Handle different cookie file formats
        if 'cookies' in cookies_data:
            simple_cookies = cookies_data['cookies']
            
            for name, value in simple_cookies.items():
                # Use domain from cookie_details if available
                domain_to_use = f"www.{hostname}"
                path_to_use = '/'
                secure_to_use = True
                
                if 'cookie_details' in cookies_data and name in cookies_data['cookie_details']:
                    details = cookies_data['cookie_details'][name]
                    domain_to_use = details.get('domain', domain_to_use)
                    path_to_use = details.get('path', path_to_use)
                    secure_to_use = details.get('secure', secure_to_use)
                
                session.cookies.set(
                    name,
                    value,
                    domain=domain_to_use,
                    path=path_to_use,
                    secure=secure_to_use
                )
        
        print(f"✓ Created authenticated session with {len(session.cookies)} cookies")
        return session
        
    except Exception as e:
        print(f"✗ Failed to create authenticated session: {e}")
        return None

def test_dl_link_extraction_authenticated():
    """Test link extraction with authenticated session"""
    
    url = "https://www.data-load.me/threads/solar-opposites-s02-german-aac-720p-web-x265-w00t.486840/"
    
    print(f"Testing AUTHENTICATED access to: {url}")
    print("=" * 80)
    
    # Create authenticated session
    session = create_authenticated_session()
    if not session:
        print("Could not create authenticated session")
        return
    
    try:
        # Fetch page with authentication
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = session.get(url, headers=headers, timeout=15)
        print(f"Response status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"Failed to fetch page")
            return
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Check authentication status
        print(f"\n=== AUTHENTICATION CHECK ===")
        
        login_indicators = [
            'Sie müssen sich registrieren',
            'Anmelden oder registrieren', 
            'Registrieren um Links zu s',
            'bitte anmelden oder registrieren'
        ]
        
        auth_success_indicators = [
            'data-logged-in="true"',
            'xf_user'
        ]
        
        login_required = False
        for indicator in login_indicators:
            if indicator in response.text:
                print(f"  ⚠️ Found login required indicator: '{indicator}'")
                login_required = True
        
        auth_success = False
        for indicator in auth_success_indicators:
            if indicator in response.text:
                print(f"  ✓ Found auth success indicator: '{indicator}'")
                auth_success = True
        
        if not login_required and auth_success:
            print("  ✓ Successfully authenticated!")
        elif login_required:
            print("  ❌ Authentication failed - login required")
        else:
            print("  ⚠️ Authentication status unclear")
        
        # Find all links
        all_links = soup.find_all('a', href=True)
        print(f"\nTotal links found: {len(all_links)}")
        
        # Container services patterns
        container_patterns = [
            r'https?://(?:www\.)?filecrypt\.(?:cc|co)/Container/[A-Za-z0-9]+\.html',
            r'https?://(?:www\.)?keeplinks\.(?:eu|org)/[A-Za-z0-9]+(?:/[A-Za-z0-9]+)*',
            r'https?://(?:www\.)?linkcrypter\.com/[A-Za-z0-9]+(?:/[A-Za-z0-9]+)*',
            r'https?://(?:www\.)?linkshare\.team/[A-Za-z0-9]+(?:/[A-Za-z0-9]+)*',
        ]
        
        # Direct hoster patterns
        direct_patterns = [
            r'https?://(?:www\.)?rapidgator\.net/file/[A-Za-z0-9]+(?:/[A-Za-z0-9._-]+)*',
            r'https?://(?:www\.)?ddownload\.com/[A-Za-z0-9]+(?:/[A-Za-z0-9._-]+)*',
            r'https?://(?:www\.)?katfile\.com/[A-Za-z0-9]+(?:/[A-Za-z0-9._-]+)*',
            r'https?://(?:www\.)?turbobit\.net/[A-Za-z0-9]+(?:/[A-Za-z0-9._-]+)*\.html?',
            r'https?://(?:www\.)?nitroflare\.com/view/[A-Za-z0-9]+(?:/[A-Za-z0-9._-]+)*',
            r'https?://(?:www\.)?uploaded\.net/file/[A-Za-z0-9]+(?:/[A-Za-z0-9._-]+)*',
        ]
        
        download_links = []
        container_links = []
        direct_links = []
        
        # Search through all links
        for link in all_links:
            href = link.get('href', '')
            
            # Check container patterns
            for pattern in container_patterns:
                if re.search(pattern, href, re.IGNORECASE):
                    container_links.append(href)
                    download_links.append(href)
            
            # Check direct patterns
            for pattern in direct_patterns:
                if re.search(pattern, href, re.IGNORECASE):
                    direct_links.append(href)
                    download_links.append(href)
        
        # Remove duplicates
        container_links = list(set(container_links))
        direct_links = list(set(direct_links))
        download_links = list(set(download_links))
        
        print(f"\n=== LINK EXTRACTION RESULTS ===")
        print(f"Container links found: {len(container_links)}")
        for i, link in enumerate(container_links[:5], 1):
            print(f"  {i}. {link}")
        if len(container_links) > 5:
            print(f"    ... and {len(container_links)-5} more")
            
        print(f"Direct hoster links found: {len(direct_links)}")
        for i, link in enumerate(direct_links[:5], 1):
            print(f"  {i}. {link}")
        if len(direct_links) > 5:
            print(f"    ... and {len(direct_links)-5} more")
        
        print(f"Total download links: {len(download_links)}")
        
        # Also search in text content for hidden links
        print(f"\n=== TEXT CONTENT SEARCH ===")
        text_matches = []
        all_patterns = container_patterns + direct_patterns
        
        for pattern in all_patterns:
            matches = re.findall(pattern, response.text, re.IGNORECASE)
            text_matches.extend(matches)
        
        text_matches = list(set(text_matches))
        print(f"Links found in text content: {len(text_matches)}")
        for i, link in enumerate(text_matches[:5], 1):
            print(f"  {i}. {link}")
        if len(text_matches) > 5:
            print(f"    ... and {len(text_matches)-5} more")
        
        # Post content analysis
        print(f"\n=== POST CONTENT ANALYSIS ===")
        post_selectors = [
            '.message-userContent',
            '.messageContent', 
            '.bbcode',
            '.post-content',
            '[data-lb-caption-desc]'
        ]
        
        for selector in post_selectors:
            elements = soup.select(selector)
            if elements:
                print(f"Found {len(elements)} elements with selector: {selector}")
                for i, element in enumerate(elements[:2]):
                    content_sample = element.get_text()[:200].replace('\n', ' ').strip()
                    print(f"  Content {i+1}: {content_sample}...")
        
        # Save debug file if no links found
        if not download_links and not text_matches:
            debug_file = f"debug_dl_authenticated_{url.split('/')[-2]}.html"
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(response.text)
            print(f"\n⚠️ No links found - saved page content to {debug_file}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

def test_dl_link_extraction():
    """Test link extraction from data-load.me thread"""
    
    url = "https://www.data-load.me/threads/solar-opposites-s02-german-aac-720p-web-x265-w00t.486840/"
    
    print(f"Testing URL: {url}")
    print("=" * 80)
    
    try:
        # Fetch page
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        print(f"Response status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"Failed to fetch page")
            return
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all links
        all_links = soup.find_all('a', href=True)
        print(f"\nTotal links found: {len(all_links)}")
        
        # Container services patterns
        container_patterns = [
            r'https?://(?:www\.)?filecrypt\.(?:cc|co)/Container/[A-Za-z0-9]+\.html',
            r'https?://(?:www\.)?keeplinks\.(?:eu|org)/[A-Za-z0-9]+(?:/[A-Za-z0-9]+)*',
            r'https?://(?:www\.)?linkcrypter\.com/[A-Za-z0-9]+(?:/[A-Za-z0-9]+)*',
            r'https?://(?:www\.)?linkshare\.team/[A-Za-z0-9]+(?:/[A-Za-z0-9]+)*',
        ]
        
        # Direct hoster patterns
        direct_patterns = [
            r'https?://(?:www\.)?rapidgator\.net/file/[A-Za-z0-9]+(?:/[A-Za-z0-9._-]+)*',
            r'https?://(?:www\.)?ddownload\.com/[A-Za-z0-9]+(?:/[A-Za-z0-9._-]+)*',
            r'https?://(?:www\.)?katfile\.com/[A-Za-z0-9]+(?:/[A-Za-z0-9._-]+)*',
            r'https?://(?:www\.)?turbobit\.net/[A-Za-z0-9]+(?:/[A-Za-z0-9._-]+)*\.html?',
            r'https?://(?:www\.)?nitroflare\.com/view/[A-Za-z0-9]+(?:/[A-Za-z0-9._-]+)*',
            r'https?://(?:www\.)?uploaded\.net/file/[A-Za-z0-9]+(?:/[A-Za-z0-9._-]+)*',
        ]
        
        download_links = []
        
        # Search through all links
        for link in all_links:
            href = link.get('href', '')
            
            # Check all patterns
            all_patterns = container_patterns + direct_patterns
            for pattern in all_patterns:
                if re.search(pattern, href, re.IGNORECASE):
                    download_links.append(href)
        
        # Remove duplicates
        download_links = list(set(download_links))
        
        print(f"\nFound {len(download_links)} download-related links")
        
        for i, link in enumerate(download_links[:10], 1):
            print(f"  {i}. {link}")
        if len(download_links) > 10:
            print(f"    ... and {len(download_links)-10} more")
        
        # Also search directly in page text
        print(f"\nSearching in page text for link patterns...")
        
        text_matches = []
        all_patterns = container_patterns + direct_patterns
        
        for pattern in all_patterns:
            matches = re.findall(pattern, response.text, re.IGNORECASE)
            text_matches.extend(matches)
        
        # Remove duplicates
        text_matches = list(set(text_matches))
        
        print(f"\nTotal unique links found via patterns: {len(text_matches)}")
        
        for i, link in enumerate(text_matches[:10], 1):
            print(f"  {i}. {link}")
        if len(text_matches) > 10:
            print(f"    ... and {len(text_matches)-10} more")
        
        # Check for login indicators
        print(f"\nChecking login indicators...")
        login_indicators = ['anmelden', 'registrieren', 'passwort', 'login']
        for indicator in login_indicators:
            if indicator.lower() in response.text.lower():
                print(f"  ⚠️ Found login indicator: '{indicator}'")
        
        # Check content visibility
        print(f"\nChecking content visibility...")
        post_areas = soup.select('.message-userContent, .messageContent, .bbcode')
        print(f"  Post content areas found: {len(post_areas)}")
        if post_areas:
            first_content = post_areas[0].get_text()[:100].replace('\n', ' ').strip()
            print(f"  First content snippet: {first_content}...")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("=== UNAUTHENTICATED TEST ===")
    test_dl_link_extraction()
    
    print("\n" + "="*80)
    print("=== AUTHENTICATED TEST ===")
    test_dl_link_extraction_authenticated() 