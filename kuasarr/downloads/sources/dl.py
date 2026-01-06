# -*- coding: utf-8 -*-
# Kuasarr
# Project by weedo078 (Fork von https://github.com/rix1337/Quasarr)
# DL Download Source - ported from Quasarr v1.26.5

import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from io import BytesIO

from PIL import Image
from bs4 import BeautifulSoup, NavigableString

from kuasarr.providers.log import info, debug
from kuasarr.providers.sessions.dl import retrieve_and_validate_session, fetch_via_requests_session, invalidate_session

hostname = "dl"

# Common TLDs to strip for mirror name comparison
COMMON_TLDS = {'.com', '.net', '.io', '.cc', '.to', '.me', '.org', '.co', '.de', '.eu', '.info'}


def normalize_mirror_name(name):
    """
    Normalize mirror name for comparison by lowercasing and removing TLDs.
    e.g., "DDownload.com" -> "ddownload", "Rapidgator.net" -> "rapidgator"
    """
    if not name:
        return ""
    normalized = name.lower().strip()
    for tld in COMMON_TLDS:
        if normalized.endswith(tld):
            normalized = normalized[:-len(tld)]
            break
    return normalized


def extract_password_from_post(soup, host):
    """
    Extract password from forum post using multiple strategies.
    Returns empty string if no password found or if explicitly marked as 'no password'.
    """
    post_text = soup.get_text()
    post_text = re.sub(r'\s+', ' ', post_text).strip()

    password_pattern = r'(?:passwort|password|pass|pw)[\s:]+([a-zA-Z0-9._-]{2,50})'
    match = re.search(password_pattern, post_text, re.IGNORECASE)

    if match:
        password = match.group(1).strip()
        if not re.match(r'^(?:download|mirror|link|episode|info|mediainfo|spoiler|hier|click|klick|kein|none|no)',
                        password, re.IGNORECASE):
            debug(f"Found password: {password}")
            return password

    no_password_patterns = [
        r'(?:passwort|password|pass|pw)[\s:]*(?:kein(?:es)?|none|no|nicht|not|nein|-|–|—)',
        r'(?:kein(?:es)?|none|no|nicht|not|nein)\s*(?:passwort|password|pass|pw)',
    ]

    for pattern in no_password_patterns:
        if re.search(pattern, post_text, re.IGNORECASE):
            debug("No password required (explicitly stated)")
            return ""

    default_password = f"www.{host}"
    debug(f"No password found, using default: {default_password}")
    return default_password


def extract_mirror_name_from_link(link_element):
    """
    Extract the mirror/hoster name from the link text or nearby text.
    """
    link_text = link_element.get_text(strip=True)
    common_non_hosters = {'download', 'mirror', 'link', 'hier', 'click', 'klick', 'code', 'spoiler'}

    # Known hoster patterns for image detection
    known_hosters = {
        'rapidgator': ['rapidgator', 'rg'],
        'ddownload': ['ddownload', 'ddl'],
        'turbobit': ['turbobit'],
        '1fichier': ['1fichier'],
    }

    # Skip if link text is a URL
    if link_text and len(link_text) > 2 and not link_text.startswith('http'):
        cleaned = re.sub(r'[^\w\s-]', '', link_text).strip().lower()
        if cleaned and cleaned not in common_non_hosters:
            main_part = cleaned.split()[0] if ' ' in cleaned else cleaned
            if 2 < len(main_part) < 30:
                return main_part

    # Check previous siblings including text nodes
    for sibling in link_element.previous_siblings:
        # Handle text nodes (NavigableString)
        if isinstance(sibling, NavigableString):
            text = sibling.strip()
            if text:
                # Remove common separators like @ : -
                cleaned = re.sub(r'[@:\-–—\s]+$', '', text).strip().lower()
                cleaned = re.sub(r'[^\w\s.-]', '', cleaned).strip()
                if cleaned and len(cleaned) > 2 and cleaned not in common_non_hosters:
                    # Take the last word as mirror name (e.g., "Rapidgator" from "Rapidgator @")
                    parts = cleaned.split()
                    if parts:
                        mirror = parts[-1]
                        if 2 < len(mirror) < 30:
                            return mirror
            continue

        # Skip non-Tag elements
        if not hasattr(sibling, 'name') or sibling.name is None:
            continue

        # Skip spoiler elements entirely
        classes = sibling.get('class', [])
        if classes and any('spoiler' in str(c).lower() for c in classes):
            continue

        # Check for images with hoster names in src/alt/data-url
        img = sibling.find('img') if sibling.name != 'img' else sibling
        if img:
            img_identifiers = (img.get('src', '') + img.get('alt', '') + img.get('data-url', '')).lower()
            for hoster, patterns in known_hosters.items():
                if any(pattern in img_identifiers for pattern in patterns):
                    return hoster

        sibling_text = sibling.get_text(strip=True).lower()
        # Skip if text is too long - likely NFO content or other non-mirror text
        if len(sibling_text) > 30:
            continue
        if sibling_text and len(sibling_text) > 2 and sibling_text not in common_non_hosters:
            cleaned = re.sub(r'[^\w\s-]', '', sibling_text).strip()
            if cleaned and 2 < len(cleaned) < 30:
                return cleaned.split()[0] if ' ' in cleaned else cleaned

    return None


def generate_status_url(href, crypter_type):
    """
    Generate a status URL for crypters that support it.
    Returns None if status URL cannot be generated.
    """
    if crypter_type == "hide":
        # hide.cx links: https://hide.cx/folder/{UUID} → https://hide.cx/state/{UUID}
        match = re.search(r'hide\.cx/(?:folder/)?([a-f0-9-]{36})', href, re.IGNORECASE)
        if match:
            uuid = match.group(1)
            return f"https://hide.cx/state/{uuid}"

    elif crypter_type == "tolink":
        # tolink links: https://tolink.to/f/{ID} → https://tolink.to/f/{ID}/s/status.png
        match = re.search(r'tolink\.to/f/([a-zA-Z0-9]+)', href, re.IGNORECASE)
        if match:
            link_id = match.group(1)
            return f"https://tolink.to/f/{link_id}/s/status.png"

    return None


def extract_status_url_from_html(link_element, crypter_type):
    """
    Extract status image URL from HTML near the link element.
    Used primarily for FileCrypt where status URLs cannot be generated.
    """
    if crypter_type != "filecrypt":
        return None

    # Look for status image in the link itself
    img = link_element.find('img')
    if img:
        for attr in ['src', 'data-url']:
            url = img.get(attr, '')
            if 'filecrypt.cc/Stat/' in url:
                return url

    # Look in siblings
    for sibling in link_element.next_siblings:
        if not hasattr(sibling, 'name') or sibling.name is None:
            continue
        if sibling.name == 'img':
            for attr in ['src', 'data-url']:
                url = sibling.get(attr, '')
                if 'filecrypt.cc/Stat/' in url:
                    return url
        # Check nested images
        nested_img = sibling.find('img') if hasattr(sibling, 'find') else None
        if nested_img:
            for attr in ['src', 'data-url']:
                url = nested_img.get(attr, '')
                if 'filecrypt.cc/Stat/' in url:
                    return url
        # Stop at next link
        if sibling.name == 'a':
            break

    return None


def build_filecrypt_status_map(soup):
    """
    Build a map of mirror names to FileCrypt status URLs.
    Handles cases where status images are in a separate section from links.
    Returns dict: {mirror_name_lowercase: status_url}
    """
    status_map = {}

    # Find all FileCrypt status images in the post
    for img in soup.find_all('img'):
        status_url = None
        for attr in ['src', 'data-url']:
            url = img.get(attr, '')
            if 'filecrypt.cc/Stat/' in url:
                status_url = url
                break

        if not status_url:
            continue

        # Look for associated mirror name in previous text/siblings
        mirror_name = None

        # Check parent's previous siblings and text nodes
        parent = img.parent
        if parent:
            # Get all previous text content before this image
            prev_text = ""
            for prev in parent.previous_siblings:
                if hasattr(prev, 'get_text'):
                    prev_text = prev.get_text(strip=True)
                elif isinstance(prev, NavigableString):
                    prev_text = prev.strip()
                if prev_text:
                    break

            # Also check text directly before within parent
            for prev in img.previous_siblings:
                if isinstance(prev, NavigableString) and prev.strip():
                    prev_text = prev.strip()
                    break
                elif hasattr(prev, 'get_text'):
                    text = prev.get_text(strip=True)
                    if text:
                        prev_text = text
                        break

            if prev_text:
                # Clean up the text to get mirror name
                cleaned = re.sub(r'[^\w\s.-]', '', prev_text).strip().lower()
                # Take last word/phrase as it's likely the mirror name
                parts = cleaned.split()
                if parts:
                    mirror_name = parts[-1] if len(parts[-1]) > 2 else cleaned

        if mirror_name and mirror_name not in status_map:
            status_map[mirror_name] = status_url
            debug(f"Mapped status image for mirror: {mirror_name} -> {status_url}")

    return status_map


def image_has_green(image_data):
    """
    Analyze image data to check if it contains green pixels.
    Returns True if any significant green is detected (indicating online status).
    """
    try:
        img = Image.open(BytesIO(image_data))
        img = img.convert('RGB')

        pixels = list(img.getdata())

        for r, g, b in pixels:
            # Check if pixel is greenish: green channel is dominant
            # and has a reasonable absolute value
            if g > 100 and g > r * 1.3 and g > b * 1.3:
                return True

        return False
    except Exception as e:
        debug(f"Error analyzing status image: {e}")
        # If we can't analyze, assume online to not skip valid links
        return True


def fetch_status_image(status_url):
    """
    Fetch a status image and return (status_url, image_data).
    Returns (status_url, None) on failure.
    """
    try:
        import requests
        response = requests.get(status_url, timeout=10)
        if response.status_code == 200:
            return (status_url, response.content)
    except Exception as e:
        debug(f"Error fetching status image {status_url}: {e}")
    return (status_url, None)


def check_links_online_status(links_with_status):
    """
    Check online status for links that have status URLs.
    Returns list of links that are online (or have no status URL to check).

    links_with_status: list of [href, identifier, status_url] where status_url can be None
    """

    links_to_check = [(i, link) for i, link in enumerate(links_with_status) if link[2]]

    if not links_to_check:
        # No status URLs to check, return all links as potentially online
        return [[link[0], link[1]] for link in links_with_status]

    # Batch fetch status images
    status_results = {}  # status_url -> has_green
    status_urls = list(set(link[2] for _, link in links_to_check))

    batch_size = 10
    for i in range(0, len(status_urls), batch_size):
        batch = status_urls[i:i + batch_size]
        with ThreadPoolExecutor(max_workers=batch_size) as executor:
            futures = [executor.submit(fetch_status_image, url) for url in batch]
            for future in as_completed(futures):
                try:
                    status_url, image_data = future.result()
                    if image_data:
                        status_results[status_url] = image_has_green(image_data)
                    else:
                        # Could not fetch, assume online
                        status_results[status_url] = True
                except Exception as e:
                    debug(f"Error checking status: {e}")

    # Filter to online links
    online_links = []

    for link in links_with_status:
        href, identifier, status_url = link
        if not status_url:
            # No status URL, include link (keeplinks case)
            online_links.append([href, identifier])
        elif status_url in status_results:
            if status_results[status_url]:
                online_links.append([href, identifier])
                debug(f"Link online: {identifier} ({href})")
            else:
                debug(f"Link offline: {identifier} ({href})")
        else:
            # Status check failed, include link
            online_links.append([href, identifier])

    return online_links


def extract_links_and_password_from_post(post_content, host):
    """
    Extract download links and password from a forum post.
    Returns links with status URLs for online checking.
    """
    links = []  # [href, identifier, status_url]
    soup = BeautifulSoup(post_content, 'html.parser')

    # Build status map for FileCrypt links (handles separated status images)
    filecrypt_status_map = build_filecrypt_status_map(soup)

    for link in soup.find_all('a', href=True):
        href = link.get('href')

        if href.startswith('/') or host in href:
            continue

        if re.search(r'filecrypt\.', href, re.IGNORECASE):
            crypter_type = "filecrypt"
        elif re.search(r'hide\.', href, re.IGNORECASE):
            crypter_type = "hide"
        elif re.search(r'keeplinks\.', href, re.IGNORECASE):
            crypter_type = "keeplinks"
        elif re.search(r'tolink\.', href, re.IGNORECASE):
            crypter_type = "tolink"
        else:
            debug(f"Unsupported link crypter/hoster found: {href}")
            continue

        mirror_name = extract_mirror_name_from_link(link)
        identifier = mirror_name if mirror_name else crypter_type

        # Get status URL - try extraction first, then status map, then generation
        status_url = extract_status_url_from_html(link, crypter_type)

        if not status_url and crypter_type == "filecrypt" and mirror_name:
            # Try to find in status map by mirror name (normalized, case-insensitive, TLD-stripped)
            mirror_normalized = normalize_mirror_name(mirror_name)
            for map_key, map_url in filecrypt_status_map.items():
                map_key_normalized = normalize_mirror_name(map_key)
                if mirror_normalized in map_key_normalized or map_key_normalized in mirror_normalized:
                    status_url = map_url
                    break

        if not status_url:
            status_url = generate_status_url(href, crypter_type)

        # Avoid duplicates (check href and identifier)
        if not any(l[0] == href and l[1] == identifier for l in links):
            links.append([href, identifier, status_url])
            status_info = f"status: {status_url}" if status_url else "no status URL"
            if mirror_name:
                debug(f"Found {crypter_type} link for mirror: {mirror_name} ({status_info})")
            else:
                debug(f"Found {crypter_type} link ({status_info})")

    password = ""
    if links:
        password = extract_password_from_post(soup, host)

    return links, password


def get_dl_download_links(shared_state, url, mirror, title, password):
    """
    KEEP THE SIGNATURE EVEN IF SOME PARAMETERS ARE UNUSED!

    DL source handler - extracts links and password from forum thread.
    Iterates through posts to find one with online links.

    Note: The password parameter is unused intentionally - password must be extracted from the post.
    """
    host = shared_state.values["config"]("Hostnames").get(hostname)
    if not host:
        return {"links": [], "password": ""}

    clean_host = host.replace("www.", "")

    sess = retrieve_and_validate_session(shared_state)
    if not sess:
        info(f"Could not retrieve valid session for {clean_host}")
        return {"links": [], "password": ""}

    try:
        response = fetch_via_requests_session(shared_state, method="GET", target_url=url, timeout=30)

        if response.status_code != 200:
            info(f"Failed to load thread page: {url} (Status: {response.status_code})")
            return {"links": [], "password": ""}

        soup = BeautifulSoup(response.text, 'html.parser')

        # Get all posts in thread
        posts = soup.select('article.message--post')
        if not posts:
            # Fallback für andere XF2 Themes
            posts = soup.select('article.message')
            
        if not posts:
            info(f"Could not find any posts in thread: {url}")
            return {"links": [], "password": ""}

        # Iterate through posts to find one with online links
        for post_index, post in enumerate(posts):
            post_content = post.select_one('div.bbWrapper')
            if not post_content:
                continue

            links_with_status, extracted_password = extract_links_and_password_from_post(str(post_content), clean_host)

            if not links_with_status:
                continue

            # Check which links are online
            online_links = check_links_online_status(links_with_status)

            if online_links:
                post_info = "first post" if post_index == 0 else f"post #{post_index + 1}"
                debug(f"Found {len(online_links)} online link(s) in {post_info} for: {title}")
                return {"links": online_links, "password": extracted_password}
            else:
                debug(f"All links in post #{post_index + 1} are offline, checking next post...")

        info(f"No online download links found in any post: {url}")
        return {"links": [], "password": ""}

    except Exception as e:
        info(f"Error extracting download links from {url}: {e}")
        invalidate_session(shared_state)
        return {"links": [], "password": ""}
