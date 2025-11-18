# -*- coding: utf-8 -*-
# Kuasarr
# Project by weedo078 (Fork von https://github.com/rix1337/Quasarr)

import re

import requests

LATEST_RELEASE_LINK = "https://github.com/weedo078/kuasarr-dl/releases/latest"


def get_version():
    return "1.0.dev.1"


def get_latest_version():
    """
    Query GitHub API for the latest release of the kuasarr repository.
    Returns the tag name string (e.g. "1.5.0" or "1.4.2a1").
    Raises RuntimeError on HTTP errors.
    """
    api_urls = [
        "https://api.github.com/repos/weedo078/kuasarr-dl/releases/latest",
        "https://api.github.com/repos/weedo078/kuasarr/releases/latest",
        "https://api.github.com/repos/rix1337/kuasarr/releases/latest",
    ]

    last_error = None
    global LATEST_RELEASE_LINK

    for api_url in api_urls:
        resp = requests.get(api_url, headers={"Accept": "application/vnd.github.v3+json"})
        if resp.status_code == 404:
            continue
        if resp.status_code != 200:
            last_error = RuntimeError(f"GitHub API error: {resp.status_code} {resp.text}")
            continue
        data = resp.json()
        tag = data.get("tag_name") or data.get("name")
        if not tag:
            last_error = RuntimeError("Could not find tag_name in GitHub response")
            continue
        tag = tag.strip()
        if tag.lower().startswith('v'):
            tag = tag[1:].lstrip('.')
        html_url = data.get("html_url")
        if html_url:
            LATEST_RELEASE_LINK = html_url
        else:
            owner_repo = api_url.split("/repos/")[-1].split("/releases")[0]
            LATEST_RELEASE_LINK = f"https://github.com/{owner_repo}/releases/tag/{tag}"
        return tag

    if last_error:
        raise last_error
    raise RuntimeError("No releases found for the configured repositories")


def _split_suffix_tokens(suffix: str):
    tokens = []
    for token in re.split(r"[._-]", suffix):
        if not token:
            continue
        if token.isdigit():
            tokens.append((0, int(token)))
        else:
            tokens.append((1, token))
    return tuple(tokens)


def _version_key(v: str):
    """Normalize a version string into a comparable tuple."""
    v = (v or "").strip()
    if not v:
        return ((), 0, ())

    base, sep, suffix = v.partition('-')
    base_parts = [part for part in base.split('.') if part]
    nums = tuple(int(part) for part in base_parts if part.isdigit())
    suffix_tokens = _split_suffix_tokens(suffix) if sep else tuple()
    is_release = 1 if not suffix_tokens else 0
    return (nums, is_release, suffix_tokens)


def is_newer(latest, current):
    """
    Return True if latest > current using semantic+alpha comparison.
    """
    return _version_key(latest) > _version_key(current)


def newer_version_available():
    """
    Check local vs. GitHub latest version.
    Returns the latest version string if a newer release is available,
    otherwise returns None.
    """
    try:
        current = get_version()
        latest = get_latest_version()
    except:
        raise
    if is_newer(latest, current):
        return latest
    return None


def create_version_file():
    version = get_version()
    base, _, suffix = version.partition('-')
    version_split = base.split('.')
    while len(version_split) < 3:
        version_split.append('0')
    major, minor, patch = (int(part) if part.isdigit() else 0 for part in version_split[:3])

    suffix_numbers = [int(tok) for tok in re.findall(r"\d+", suffix)] if suffix else []
    build = suffix_numbers[0] if suffix_numbers else 0
    version_info = [
        "VSVersionInfo(",
        "  ffi=FixedFileInfo(",
        f"    filevers=({major}, {minor}, {patch}, {build})",
        f"    prodvers=({major}, {minor}, {patch}, {build})",
        "    mask=0x3f,",
        "    flags=0x0,",
        "    OS=0x4,",
        "    fileType=0x1,",
        "    subtype=0x0,",
        "    date=(0, 0)",
        "    ),",
        "  kids=[",
        "    StringFileInfo(",
        "      [",
        "      StringTable(",
        "        u'040704b0',",
        "        [StringStruct(u'CompanyName', u'RiX & weedo078'),",
        "        StringStruct(u'FileDescription', u'kuasarr'),",
        f"        StringStruct(u'FileVersion', u'{major}.{minor}.{patch}.{build}'),",
        "        StringStruct(u'InternalName', u'kuasarr'),",
        "        StringStruct(u'LegalCopyright', u'Copyright Â© RiX & weedo078'),",
        "        StringStruct(u'OriginalFilename', u'kuasarr.exe'),",
        "        StringStruct(u'ProductName', u'kuasarr'),",
        f"        StringStruct(u'ProductVersion', u'{major}.{minor}.{patch}.{build}')])",
        "      ]),",
        "    VarFileInfo([VarStruct(u'Translation', [1031, 1200])])",
        "  ]",
        ")"
    ]
    with open('file_version_info.txt', 'w', encoding='utf-8') as fh:
        fh.write("\n".join(version_info))


if __name__ == '__main__':
    print(get_version())
    create_version_file()



