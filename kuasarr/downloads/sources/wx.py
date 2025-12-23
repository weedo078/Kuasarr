# -*- coding: utf-8 -*-
# Kuasarr WX Integration
# Based on PR #159 from rix1337/Quasarr

import re

import requests
from bs4 import BeautifulSoup

from ...providers.log import info, debug

hostname = "wx"


def extract_links_from_page(page_html, host):
    """
    Extract download links from a detail page.
    Only filecrypt and hide are supported - other link crypters will cause a warning.
    """
    links = []
    soup = BeautifulSoup(page_html, 'html.parser')

    for link in soup.find_all('a', href=True):
        href = link.get('href')

        # Skip internal links
        if href.startswith('/') or host in href:
            continue

        # ONLY support filecrypt and hide
        if re.search(r'filecrypt\.cc', href, re.IGNORECASE):
            if href not in links:
                links.append(href)
        elif re.search(r'hide\.', href, re.IGNORECASE):
            if href not in links:
                links.append(href)
        elif re.search(r'(linksnappy|relink\.us|links\.snahp|rapidgator|uploaded\.net|nitroflare|ddownload\.com|filefactory|katfile|mexashare|keep2share|mega\.nz|1fichier)', href, re.IGNORECASE):
            # These crypters/hosters are NOT supported yet
            info(f"Unsupported link crypter/hoster found: {href}")
            info(f"Currently only filecrypt.cc and hide.* are supported. Other crypters may be added later.")

    return links


def get_wx_download_links(shared_state, url, mirror, title):
    """
    Get download links from a WX detail page.

    Returns:
        dict with 'links', 'password', and 'title'
    """
    host = shared_state.values["config"]("Hostnames").get(hostname)
    if not host:
        debug(f"WX hostname not configured")
        return {}

    headers = {
        'User-Agent': shared_state.values.get("user_agent",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
    }

    try:
        session = requests.Session()
        response = session.get(url, headers=headers, timeout=30)

        if response.status_code != 200:
            info(f"{hostname.upper()}: Failed to load page: {url} (Status: {response.status_code})")
            return {}

        # Extract slug from URL
        slug_match = re.search(r'/detail/([^/]+)', url)
        if slug_match:
            slug = slug_match.group(1)

            # Try API (start/d/<slug>) – matches Upstream behaviour
            api_url = f'https://api.{host}/start/d/{slug}'
            try:
                api_headers = {
                    'User-Agent': shared_state.values["user_agent"],
                    'Accept': 'application/json'
                }
                debug(f"{hostname.upper()}: Fetching API data from: {api_url}")
                api_response = session.get(api_url, headers=api_headers, timeout=30)
                if api_response.status_code == 200:
                    data = api_response.json()

                    if 'item' in data and 'releases' in data['item']:
                        releases = data['item']['releases']

                        # Find release matching title
                        matching_release = None
                        for release in releases:
                            if release.get('fulltitle') == title:
                                matching_release = release
                                break

                        if matching_release:
                            crypted_links = matching_release.get('crypted_links', {}) or {}
                            links = []

                            def _append_if_supported(link, hoster_label):
                                if re.search(r'hide\.', link, re.IGNORECASE) or re.search(r'filecrypt\.', link, re.IGNORECASE):
                                    links.append(link)
                                    debug(f"{hostname.upper()}: Found {hoster_label} link")
                                else:
                                    info(f"{hostname.upper()}: Unsupported link from API: {link}")

                            if mirror:
                                matched_hoster = None
                                for hoster in crypted_links.keys():
                                    if mirror.lower() in hoster.lower() or hoster.lower() in mirror.lower():
                                        matched_hoster = hoster
                                        break
                                if matched_hoster:
                                    _append_if_supported(crypted_links.get(matched_hoster, ""), matched_hoster)
                                else:
                                    info(f"{hostname.upper()}: Mirror '{mirror}' not found in available hosters: {list(crypted_links.keys())}")
                            else:
                                for hoster, link in crypted_links.items():
                                    _append_if_supported(link, hoster)

                            if links:
                                password = f"www.{host}"
                                return {"links": links, "password": password, "title": title}
                            else:
                                info(f"{hostname.upper()}: No supported crypted links found for: {title}")
                                return {}
                        else:
                            info(f"{hostname.upper()}: No release found matching title: {title}")
                            return {}
            except Exception as e:
                debug(f"{hostname.upper()}: API fetch error: {e}")

        # Fallback to HTML parsing
        links = extract_links_from_page(response.text, host)

        if not links:
            info(f"{hostname.upper()}: No supported download links found in page: {url}")
            return {}

        password = f"www.{host}"
        debug(f"{hostname.upper()}: Found {len(links)} download link(s) via HTML for: {title}")

        return {
            "links": links,
            "password": password,
            "title": title
        }

    except Exception as e:
        info(f"{hostname.upper()}: Error extracting download links from {url}: {e}")
        return {}
