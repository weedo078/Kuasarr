# -*- coding: utf-8 -*-
# Quasarr DL Integration - Persistent Session Version
import re
import os
import json
import requests
from bs4 import BeautifulSoup

from ...providers.log import debug, info
from ...providers.sessions import dl as dl_session

# Request counter for session refresh
_request_count = 0

def startup_initialize_session(shared_state):
    """Initialize DL session on startup."""
    session = dl_session.retrieve_and_validate_session(shared_state)
    if session:
        info("DL startup session initialization successful")
    else:
        info("DL startup session initialization failed")





def get_dl_session(shared_state):
    """Get valid DL session using persistent session management."""
    global _request_count
    
    # Session refresh every 50 requests to prevent stale sessions
    _request_count += 1
    if _request_count % 50 == 0:
        debug("Refreshing DL session after 50 requests")
        dl_session.invalidate_session(shared_state)
    
    return dl_session.retrieve_and_validate_session(shared_state)


def extract_download_links_and_password(content, search_string):
    """Extract download links and password from page content."""
    links = []
    password = None
    
    # Container services (higher priority) - KORRIGIERTE PATTERNS!
    container_patterns = [
        r'https?://(?:www\.)?filecrypt\.(?:cc|co)/Container/[A-Za-z0-9]+\.html',
        r'https?://(?:www\.)?keeplinks\.(?:eu|org)/[A-Za-z0-9]+(?:/[A-Za-z0-9]+)*',
        r'https?://(?:www\.)?linkcrypter\.com/[A-Za-z0-9]+(?:/[A-Za-z0-9]+)*',
        r'https?://(?:www\.)?linkshare\.team/[A-Za-z0-9]+(?:/[A-Za-z0-9]+)*',
    ]
    
    # Direct hoster patterns - KORRIGIERTE PATTERNS!
    direct_patterns = [
        r'https?://(?:www\.)?rapidgator\.net/file/[A-Za-z0-9]+(?:/[A-Za-z0-9._-]+)*',
        r'https?://(?:www\.)?ddownload\.com/[A-Za-z0-9]+(?:/[A-Za-z0-9._-]+)*',
        r'https?://(?:www\.)?katfile\.com/[A-Za-z0-9]+(?:/[A-Za-z0-9._-]+)*',
        r'https?://(?:www\.)?turbobit\.net/[A-Za-z0-9]+(?:/[A-Za-z0-9._-]+)*\.html?',
        r'https?://(?:www\.)?nitroflare\.com/view/[A-Za-z0-9]+(?:/[A-Za-z0-9._-]+)*',
        r'https?://(?:www\.)?uploaded\.net/file/[A-Za-z0-9]+(?:/[A-Za-z0-9._-]+)*',
    ]
    
    # Extract container links first (higher priority)
    for pattern in container_patterns:
        found_links = re.findall(pattern, content, re.IGNORECASE)
        links.extend(found_links)
    
    # Extract direct hoster links
    for pattern in direct_patterns:
        found_links = re.findall(pattern, content, re.IGNORECASE)
        links.extend(found_links)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_links = []
    for link in links:
        if link not in seen:
            seen.add(link)
            unique_links.append(link)
    
    # Extract password from content
    password_patterns = [
        # German patterns
        r'<b>Passwort:</b>\s*<br\s*/?>[\s\S]*?<b><span[^>]*>([^<]+)</span></b>',
        r'<b>Passwort:</b>[\s\S]*?<span[^>]*>([^<]+)</span>',
        r'<b>Passwort:</b>\s*<br\s*/?>[\s\S]*?<b>([^<]+)</b>',
        r'<b>Passwort:</b>\s*([a-zA-Z0-9_\-\.]+)',
        r'Passwort:\s*<[^>]*>([^<]+)<',
        r'Passwort:\s*([a-zA-Z0-9_\-\.]+)',
        
        # English patterns
        r'<b>Password:</b>\s*<br\s*/?>[\s\S]*?<b><span[^>]*>([^<]+)</span></b>',
        r'<b>Password:</b>[\s\S]*?<span[^>]*>([^<]+)</span>',
        r'<b>Password:</b>\s*<br\s*/?>[\s\S]*?<b>([^<]+)</b>',
        r'<b>Password:</b>\s*([a-zA-Z0-9_\-\.]+)',
        r'Password:\s*<[^>]*>([^<]+)<',
        r'Password:\s*([a-zA-Z0-9_\-\.]+)',
        
        # Common patterns
        r'PW:\s*([a-zA-Z0-9_\-\.]+)',
        r'Pass:\s*([a-zA-Z0-9_\-\.]+)',
    ]
    
    for pattern in password_patterns:
        match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
        if match:
            password = match.group(1).strip()
            debug(f"Found password using pattern: {password}")
            break
    
    debug(f"Extracted {len(unique_links)} download links and password: {'***' if password else 'None'}")
    return unique_links, password


def extract_download_links(content, search_string):
    """Extract download links from page content (backward compatibility)."""
    links, _ = extract_download_links_and_password(content, search_string)
    return links


def get_dl_download_link(shared_state, url, search_string):
    """Get download links and password from DL source."""
    hostname = shared_state.values["config"]("Hostnames").get("dl")
    if not hostname:
        info("DL hostname not configured")
        return []
    
    session = get_dl_session(shared_state)
    if not session:
        info(f"Could not get valid session for {hostname}")
        return []
    
    headers = {
        'User-Agent': shared_state.values["user_agent"],
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'de,en-US;q=0.7,en;q=0.3',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    try:
        debug(f"Fetching DL page: {url}")
        debug(f"Session cookies: {len(session.cookies)} cookies available")
        response = session.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Debug: Check if we're actually logged in
        content_lower = response.text.lower()
        if any(indicator in content_lower for indicator in ['<input name="login"', '<input name="password"', 'form-login', 'btn-login']):
            debug("WARNING: Download page shows login form - session may be invalid!")
            # Invalidate session and try to recreate
            dl_session.invalidate_session(shared_state)
            session = get_dl_session(shared_state)
            if session:
                response = session.get(url, headers=headers, timeout=30)
            response.raise_for_status()
        
        # Debug: Check for common login indicators
        if 'anmelden' in content_lower or 'login' in content_lower:
            debug("WARNING: Download page contains login indicators!")
        
        debug(f"Response status: {response.status_code}, Content length: {len(response.text)}")
        
        # Extract links and password from page content
        links, password = extract_download_links_and_password(response.text, search_string)
        
        # Also check if there are links in post content
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for post content areas
        post_selectors = [
            '.message-userContent',
            '.messageContent',
            '.bbcode',
            '.post-content',
            '[data-lb-caption-desc]'
        ]
        
        for selector in post_selectors:
            post_elements = soup.select(selector)
            for element in post_elements:
                post_links, post_password = extract_download_links_and_password(str(element), search_string)
                for link in post_links:
                    if link not in links:
                        links.append(link)
                # Use password from post content if we haven't found one yet
                if not password and post_password:
                    password = post_password
        
        if links:
            info(f"Found {len(links)} download links for '{search_string}' with password: {'***' if password else 'None'}")
            return {"links": links, "password": password}
        else:
            debug(f"No download links found for '{search_string}'")
            return {"links": [], "password": None}
        
    except Exception as e:
        info(f"Error fetching DL download: {e}")
        return {"links": [], "password": None}


def get_all_download_links(shared_state, urls, search_string):
    """Get download links from multiple DL URLs."""
    all_links = []
    
    for url in urls:
        try:
            links = get_dl_download_link(shared_state, url, search_string)
            all_links.extend(links)
        except Exception as e:
            debug(f"Error processing URL {url}: {e}")
            continue
    
    # Remove duplicates
    unique_links = list(set(all_links))
    
    if unique_links:
        info(f"Total found {len(unique_links)} unique download links")
    
    return unique_links


def check_filecrypt_needs_captcha(shared_state, filecrypt_url):
    """Check if a FileCrypt link needs a captcha or can be processed directly."""
    try:
        session = dl_session.retrieve_and_validate_session(shared_state)
        if not session:
            debug("No valid DL session for FileCrypt check")
            return True  # Default to captcha if no session
        
        headers = {'User-Agent': shared_state.values["user_agent"]}
        response = session.get(filecrypt_url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            debug(f"FileCrypt check failed with status {response.status_code}")
            return True
            
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Check for circle captcha (needs solving)
        circle_captcha = bool(soup.find_all("div", {"class": "circle_captcha"}))
        if circle_captcha:
            debug(f"FileCrypt {filecrypt_url} requires circle captcha")
            return True
            
        # Check for CNL form (can be processed directly)
        cnl_form = bool(soup.find("form", {"class": "cnlform"}))
        if cnl_form:
            debug(f"FileCrypt {filecrypt_url} has CNL form - no captcha needed")
            return False
            
        # Check for offline indicators
        if "/404.html" in response.url or "container" not in response.text.lower():
            debug(f"FileCrypt {filecrypt_url} appears to be offline")
            return True  # Let captcha handler deal with offline links
            
        # Default to captcha if unsure
        debug(f"FileCrypt {filecrypt_url} status unclear - defaulting to captcha")
        return True
        
    except Exception as e:
        debug(f"Error checking FileCrypt {filecrypt_url}: {e}")
        return True  # Default to captcha on error 