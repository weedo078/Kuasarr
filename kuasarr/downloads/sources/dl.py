# -*- coding: utf-8 -*-
# Kuasarr DL Integration
# Based on PR #159 from rix1337/Quasarr

import re
from bs4 import BeautifulSoup

from ...providers.log import debug, info
from ...providers.sessions.dl import fetch_via_requests_session, invalidate_session, retrieve_and_validate_session

hostname = "dl"


def startup_initialize_session(shared_state):
    """Initialize DL session on startup."""
    session = retrieve_and_validate_session(shared_state)
    if session:
        info("DL startup session initialization successful")
    else:
        info("DL startup session initialization failed")


def extract_links_from_post(post_html, host):
    """
    Extract download links from a forum post.
    Supports:
    - Direct hosters: rapidgator, uploaded, ddownload, nitroflare, turbobit, 1fichier, katfile, mexashare
    - Container services: filecrypt, hide, keeplinks
    
    Returns dict with 'direct' and 'protected' links.
    - direct: list of direct hoster URLs (can be sent to JDownloader immediately)
    - protected: list of [url, hoster_name] for container services (need CAPTCHA)
    """
    direct_links = []
    protected_links = []
    soup = BeautifulSoup(post_html, 'html.parser')

    # Direct hosters (premium download services) - can be sent directly to JDownloader
    direct_hosters = {
        r'rapidgator\.net': 'Rapidgator',
        r'uploaded\.net': 'Uploaded', 
        r'uploaded\.to': 'Uploaded',
        r'ul\.to': 'Uploaded',
        r'ddownload\.com': 'DDownload',
        r'nitroflare\.com': 'Nitroflare',
        r'turbobit\.net': 'Turbobit',
        r'1fichier\.com': '1Fichier',
        r'katfile\.com': 'Katfile',
        r'mexashare\.com': 'Mexashare',
        r'depositfiles\.com': 'Depositfiles',
        r'filefactory\.com': 'Filefactory',
    }
    
    # Container/crypter services - need CAPTCHA solving
    container_services = {
        r'filecrypt\.cc': 'Filecrypt',
        r'filecrypt\.co': 'Filecrypt',
        r'hide\.': 'Hide',
        r'keeplinks\.org': 'Keeplinks',
        r'keeplinks\.eu': 'Keeplinks',
    }

    for link in soup.find_all('a', href=True):
        href = link.get('href')

        # Skip internal forum links
        if href.startswith('/') or host in href:
            continue

        # Check for direct hosters first (higher priority)
        is_direct = False
        for pattern, hoster_name in direct_hosters.items():
            if re.search(pattern, href, re.IGNORECASE):
                if href not in direct_links:
                    direct_links.append(href)
                    debug(f"Direct hoster link found ({hoster_name}): {href}")
                is_direct = True
                break
        
        if is_direct:
            continue
            
        # Check for container services (need CAPTCHA)
        for pattern, service_name in container_services.items():
            if re.search(pattern, href, re.IGNORECASE):
                # Store as [url, service_name] for CAPTCHA queue
                if not any(p[0] == href for p in protected_links):
                    protected_links.append([href, service_name])
                    debug(f"Container link found ({service_name}): {href}")
                break

    if direct_links:
        info(f"Found {len(direct_links)} direct hoster link(s) and {len(protected_links)} container link(s)")
    elif protected_links:
        info(f"Found {len(protected_links)} container link(s), no direct hoster links")
    
    return {
        "direct": direct_links,
        "protected": protected_links
    }


def extract_password_from_post(post_content, host, title=""):
    """
    Extract password from post content.
    Uses hardcoded passwords for known release groups, then pattern matching,
    with explicit "no password" detection before falling back to default.
    """
    # Hardcoded passwords for known release groups (check title)
    title_lower = title.lower() if title else ""
    
    known_group_passwords = {
        # w00t / woot / the wooter
        'w00t': 'w00t',
        'woot': 'w00t',
        'thewooter': 'w00t',
        'the wooter': 'w00t',
        'the-wooter': 'w00t',
        # funxd (password is "funxd" - first part of hostname, like in fx.py)
        'FuN': 'funxd',
        'funxd': 'funxd',
    }
    
    # Check if title contains any known release group
    for group_pattern, password in known_group_passwords.items():
        if group_pattern in title_lower:
            info(f"Password for release group '{group_pattern}': {password}")
            return password
    
    # Fallback: Try to extract from post content
    post_text = post_content.get_text() if hasattr(post_content, 'get_text') else str(post_content)
    # Normalize whitespace to avoid false negatives
    post_text = re.sub(r'\s+', ' ', post_text).strip()

    # Upstream Strategy: Label + value, skip common non-password tokens
    label_pattern = r'(?:passwort|password|pass|pw)[\s:]+([a-zA-Z0-9._-]{2,50})'
    match = re.search(label_pattern, post_text, re.IGNORECASE)
    if match:
        candidate = match.group(1).strip()
        skip_prefix = r'^(?:download|mirror|link|episode|info|mediainfo|spoiler|hier|click|klick|kein|none|no)'
        if not re.match(skip_prefix, candidate, re.IGNORECASE):
            debug(f"Password extracted from post (label strategy): '{candidate}'")
            return candidate
    
    password_patterns = [
        r'(?:Passwort|Password|Pass|PW)\s*[:\.\-=]+\s*([^\s<\n\r]+)',
        r'(?:Passwort|Password|Pass|PW)\.+\s*[:\.\-=]*\s*([^\s<\n\r]+)',
        r'(?:Entpacken|Unpack|Extract)\s*[:\.\-=]+\s*([^\s<\n\r]+)',
        r'\[code\]\s*([^\s\[\]]{3,50})\s*\[/code\]',  # common forum code tags
    ]

    for pattern in password_patterns:
        match = re.search(pattern, post_text, re.IGNORECASE)
        if match and match.group(1):
            extracted_pw = match.group(1).strip()
            if extracted_pw and len(extracted_pw) >= 3 and extracted_pw.lower() not in ['the', 'ist', 'und', 'for']:
                debug(f"Password extracted from post: '{extracted_pw}'")
                return extracted_pw

    # Explicit "no password" indicators -> return empty string (do not force default)
    no_password_patterns = [
        r'(?:passwort|password|pass|pw)\s*[:\s-]*(?:kein(?:es)?|none|no|nicht|not|nein)',
        r'(?:kein(?:es)?|none|no|nicht|not|nein)\s*(?:passwort|password|pass|pw)',
    ]
    for pattern in no_password_patterns:
        if re.search(pattern, post_text, re.IGNORECASE):
            debug("No password required (explicitly stated)")
            return ""
    
    # Default password (forum hostname)
    default_pw = f"www.{host}"
    debug(f"No password found, using default: {default_pw}")
    return default_pw


def get_dl_download_links(shared_state, url, mirror, title):
    """
    Get download links from a DL thread.
    
    Args:
        shared_state: Shared state object
        url: Thread URL
        mirror: Mirror (not used for DL)
        title: Release title
    
    Returns:
        dict with:
        - 'direct': list of direct hoster URLs (can be sent to JDownloader immediately)
        - 'protected': list of [url, hoster_name] for container services (need CAPTCHA)
        - 'password': extracted password
        - 'title': release title
    """
    host = shared_state.values["config"]("Hostnames").get(hostname)
    if not host:
        info("DL hostname not configured")
        return {}

    sess = retrieve_and_validate_session(shared_state)
    if not sess:
        info(f"Could not retrieve valid session for {host}")
        return {}

    try:
        response = fetch_via_requests_session(shared_state, method="GET",
                                              target_url=url,
                                              timeout=30)

        if not response or response.status_code != 200:
            info(f"Failed to load thread page: {url} (Status: {response.status_code if response else 'None'})")
            return {}

        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract links from the first post (original post)
        first_post = soup.select_one('article.message--post')
        if not first_post:
            info(f"Could not find first post in thread: {url}")
            return {}

        post_content = first_post.select_one('div.bbWrapper')
        if not post_content:
            info(f"Could not find post content in thread: {url}")
            return {}

        link_data = extract_links_from_post(str(post_content), host)
        direct_links = link_data.get("direct", [])
        protected_links = link_data.get("protected", [])

        if not direct_links and not protected_links:
            info(f"No supported download links found in thread: {url}")
            return {}

        password = extract_password_from_post(post_content, host, title)

        total = len(direct_links) + len(protected_links)
        debug(f"Found {total} download link(s) for: {title} ({len(direct_links)} direct, {len(protected_links)} protected)")

        return {
            "direct": direct_links,
            "protected": protected_links,
            "password": password,
            "title": title
        }

    except Exception as e:
        info(f"Error extracting download links from {url}: {e}")
        invalidate_session(shared_state)
        return {}


# Legacy function for backward compatibility
def get_dl_download_link(shared_state, url, search_string):
    """Legacy wrapper - use get_dl_download_links instead."""
    result = get_dl_download_links(shared_state, url, None, search_string)
    return result 
