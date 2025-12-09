# -*- coding: utf-8 -*-
# Kuasarr
# Project by weedo078 (Fork von https://github.com/rix1337/Quasarr)

"""
Utility functions for string sanitization and conversion.
"""

import re

__all__ = [
    "sanitize_title",
    "sanitize_string",
    "convert_to_mb",
]


def sanitize_title(title: str) -> str:
    """
    Sanitize a release title for use as filename/package name.
    
    - Replaces umlauts with ASCII equivalents
    - Removes non-ASCII characters
    - Replaces spaces with dots
    - Removes invalid characters
    """
    umlaut_map = {
        "Ä": "Ae", "ä": "ae",
        "Ö": "Oe", "ö": "oe",
        "Ü": "Ue", "ü": "ue",
        "ß": "ss"
    }
    for umlaut, replacement in umlaut_map.items():
        title = title.replace(umlaut, replacement)

    title = title.encode("ascii", errors="ignore").decode()

    # Replace slashes and spaces with dots
    title = title.replace("/", "").replace(" ", ".")
    title = title.strip(".")  # no leading/trailing dots
    title = title.replace(".-.", "-")  # .-. → -

    # Finally, drop any chars except letters, digits, dots, hyphens, ampersands
    title = re.sub(r"[^A-Za-z0-9.\-&]", "", title)

    # Remove any repeated dots
    title = re.sub(r"\.{2,}", ".", title)
    return title


def sanitize_string(s: str) -> str:
    """
    Sanitize a string for comparison/matching.
    
    - Converts to lowercase
    - Replaces separators with spaces
    - Replaces umlauts
    - Removes special characters
    - Removes season/episode patterns
    - Removes articles
    """
    s = s.lower()

    # Remove dots / pluses
    s = s.replace('.', ' ')
    s = s.replace('+', ' ')
    s = s.replace('_', ' ')
    s = s.replace('-', ' ')

    # Umlauts
    s = re.sub(r'ä', 'ae', s)
    s = re.sub(r'ö', 'oe', s)
    s = re.sub(r'ü', 'ue', s)
    s = re.sub(r'ß', 'ss', s)

    # Remove special characters
    s = re.sub(r'[^a-zA-Z0-9\s]', '', s)

    # Remove season and episode patterns
    s = re.sub(r'\bs\d{1,3}(e\d{1,3})?\b', '', s)

    # Remove German and English articles
    articles = r'\b(?:der|die|das|ein|eine|einer|eines|einem|einen|the|a|an|and)\b'
    s = re.sub(articles, '', s, flags=re.IGNORECASE)

    # Replace obsolete titles
    s = s.replace('navy cis', 'ncis')

    # Remove extra whitespace
    s = ' '.join(s.split())

    return s


def convert_to_mb(item: dict) -> int:
    """
    Convert size from various units to megabytes.
    
    Args:
        item: Dict with 'size' and 'sizeunit' keys
        
    Returns:
        Size in megabytes as integer
    """
    size = float(item['size'])
    unit = item['sizeunit'].upper()

    if unit == 'B':
        size_b = size
    elif unit == 'KB':
        size_b = size * 1024
    elif unit == 'MB':
        size_b = size * 1024 * 1024
    elif unit == 'GB':
        size_b = size * 1024 * 1024 * 1024
    elif unit == 'TB':
        size_b = size * 1024 * 1024 * 1024 * 1024
    else:
        raise ValueError(f"Unsupported size unit {item['name']} {item['size']} {item['sizeunit']}")

    size_mb = size_b / (1024 * 1024)
    return int(size_mb)
