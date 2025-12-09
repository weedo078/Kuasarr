# DL & WX Integration Improvement Plan

## Status: ✅ COMPLETED (2025-12-09)

## Context
Based on PR #159 from rix1337/Quasarr, we improved the DL integration and added WX support.

## Key Changes from PR #159

### 1. DL Session: Username/Password instead of Cookies
**Current (Kuasarr):** Uses cookie files (`dl_cookies.json`)
**New (PR):** Uses username/password login via config

Config section:
```ini
[DL]
username = your_username
password = your_password
```

### 2. Link Extraction: Only filecrypt.cc and hide.*
**Current:** Extracts many different hosters/crypters
**New:** Only supports `filecrypt.cc` and `hide.*` - other crypters log a warning

### 3. WX (formerly WCX) Integration
New source for warez.cx with:
- API-based link extraction (`https://api.{host}/release/{slug}`)
- HTML fallback parsing
- Same link filtering (only filecrypt/hide)

## Implementation Steps

### Phase 1: Update DL Session to use Username/Password
1. Modify `kuasarr/providers/sessions/dl.py`:
   - Add login via username/password
   - Keep cookie file support as fallback
   - Use XenForo login endpoint

2. Update config handling in `kuasarr/__init__.py`:
   - Check for `[DL]` section with `username` and `password`
   - Prompt for credentials if missing

3. Update UI in `kuasarr/api/config.py`:
   - Add DL credentials configuration

### Phase 2: Improve Link Extraction
1. Update `kuasarr/downloads/sources/dl.py`:
   - Simplify to only extract filecrypt.cc and hide.* links
   - Log warning for unsupported crypters
   - Use hostname from config instead of hardcoded values

### Phase 3: Add WX Integration
1. Create `kuasarr/downloads/sources/wx.py`:
   - API-based link extraction
   - HTML fallback
   - Same link filtering

2. Create `kuasarr/providers/sessions/wx.py`:
   - Simple requests session (no login required)

3. Update `kuasarr/downloads/__init__.py`:
   - Add WX handler
   - Add WX flag

4. Update config/UI:
   - Add WX hostname option

### Phase 4: Testing & Documentation
1. Test DL login with username/password
2. Test link extraction
3. Test WX integration
4. Update CHANGELOG

## Files to Modify/Create

### Modify:
- `kuasarr/providers/sessions/dl.py` - Add username/password login
- `kuasarr/downloads/sources/dl.py` - Simplify link extraction
- `kuasarr/downloads/__init__.py` - Add WX handler
- `kuasarr/__init__.py` - Add DL/WX credential checks
- `kuasarr/api/config.py` - Add DL/WX config UI

### Create:
- `kuasarr/downloads/sources/wx.py` - WX source
- `kuasarr/providers/sessions/wx.py` - WX session (optional)

## Notes
- Keep backward compatibility with cookie files
- Use 2-letter aliases (DL, WX) as per PR feedback
- Only support filecrypt.cc and hide.* for now
- Other crypters can be added later
