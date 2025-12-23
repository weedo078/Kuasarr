# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [1.8.3] - 2025-12-23

### Changed
- Web UI authentication can be configured via `kuasarr.ini` (no CLI/env required).

---

## [1.8.2] - 2025-12-23

### Added
- Docs: Ultra.cc installation guide and systemd user update guide (GitHub release wheel workflow).

### Changed
- WX source: removed feed limit (no artificial `limit=50`) in API call.
- DL/NK/NX logging: normalized log level entries.
- Packaging: `version.json` included in package; `__main__.py` entrypoint allows `python -m kuasarr`.

### Fixed
- DL debug spam reduced; consistent logging schema across integrations.

---

## [1.8.1] - 2025-12-22

### Added
- **Multi-arch Docker images**: Published images for `linux/amd64`, `linux/arm64`, and `linux/arm/v7`.

### Changed
- Version set to 1.8.1

---

## [1.8.0] - 2025-12-22

### Added
- **DL/WX upstream features**: Improved DL password detection (label strategy, code tags, “no password”), real DL RSS feeds (replacing dummy), WX API flow.
- **hide.cx pipeline**: More robust decryption (accepts string URLs, dedupes), DL fallback to CAPTCHA queue on failure.

### Fixed
- **Archive/Download status**: Better archive detection, multiple “extraction ok” strings, bytes/ETA finalization only for non-archives.
- **NK fix**: Mirror whitelist rapidgator/ddownload, ddl.to normalization, mirror from button text.
- **MyJD**: Retry/backoff on offline/maintenance.

### Changed
- Version set to 1.8.0
- **Search/Feed review**: Upstream v1.21.1 feed/pagination refactor reviewed; Kuasarr uses a custom search/feed flow, no changes required.

---

## [1.7.0] - 2025-12-16

### Added
- **HE Source Integration**: Added `he` as new supported hostname/source for search + downloads
  - Based on upstream Quasarr v.1.19.0
  - Supports IMDb search and feed
  - Automatic content-protector form handling

---

## [1.6.2] - 2025-12-16

### Fixed
- **Port Handling**: Fixed CLI argument `--port` not being evaluated in Docker mode
- **Error Message**: Dynamic port in Docker startup error message

---

## [1.6.1] - 2025-12-16

### Changed
- **Default Port**: Changed from `8080` to `9999`
  - Updated `kuasarr/__init__.py`, `web_server.py`, `Dockerfile`, `setup.py`
  - Docker `EXPOSE` and `ENTRYPOINT` now use port `9999`

---

## [1.6.0] - 2025-12-15

### Added
- **NK Source Integration**: Added `nk` as a new supported hostname/source for search + downloads.
- **Captcha Bypass Setup Guide**: Added first-time setup instructions (Tampermonkey + userscript) with hide/show toggle (stored in `localStorage`).
- **Userscript Endpoint**: `GET /captcha/kuasarr.user.js` serves the Tampermonkey userscript used for quick link transfer.

---

## [1.5.0] - 2025-12-10

### Added
- **Progressive Web App**: New `manifest.webmanifest`, service worker (`sw.js`), offline fallback page, and dedicated icons provide installable experience across desktop/mobile.
- **PWA Install Page**: `/pwa-install` guides users through installation and offers native install prompt where supported.
- **Windows EXE Onboarding**: First run of the packaged EXE now auto-opens the PWA install page in the default browser.

### Changed
- **HTML Templates**: Added PWA meta tags (`theme-color`, `apple-mobile-web-app-*`), manifest link, and service worker registration script.
- **Static Serving**: Setup and main Bottle apps serve the new PWA assets (manifest, service worker, install page) with correct MIME types.
- **Configuration**: New `[PWA]` section tracks whether the install prompt was already shown to avoid repeated popups.

---

## [1.4.2] - 2025-12-10

### Changed
- **Keeplinks Decryption**:
  - Retry logic for DBC captchas with automatic reporting of incorrect solutions
  - Improved link detection (ignores ad/affiliate links, specifically searches for `form_box_title`/`selecttext`)
  - Keeplinks is now fed back into the direct link flow after successful decryption

### Fixed
- **DBC Dispatcher**: Keeplinks links are correctly detected, ad links (e.g. `ddownload.com/free...`) are filtered
- **Linkcrypters/Keeplinks**: Session remains valid during CAPTCHA; link list is reliably extracted

---

## [1.4.1] - 2025-12-10

### Fixed
- **Captcha Bypass UI**: Fixed TypeError caused by inline dict usage in `render_button`
- **DBC Dispatcher**: Stale job detection resets processing jobs hanging >2 min
- **CF Bypass**: Fixed error handling when FS returns error dict
- **CutCaptcha**: Now uses official `DBC-official` library (HTTP API returns 501)
- **reCAPTCHA v2**: Fixed HTTP API implementation (type=4, token_params JSON)

### Added
- **Dependency**: `DBC-official>=4.6.0` for CutCaptcha support

### Changed
- **DBC Client**: 
  - CutCaptcha uses official library (HTTP API doesn't support type=19)
  - reCAPTCHA/Image captchas use own HTTP API implementation

### Improved
- Added detailed logging for CF bypass status
- Added progress logs for each link processed
- Added Circle-Captcha coordinate logging & validation

---

## [1.4.0] - 2025-12-09

### Added
- **DBC Integration**: Full captcha solving via DBC API
  - Replaces Sponsors_Helper completely
  - Supports image captchas, reCAPTCHA v2, CutCaptcha, and Circle-Captcha (coordinates)
  - Encrypted credential storage in `kuasarr.ini`
  - Environment variable support: `DBC_USERNAME`, `DBC_PASSWORD`, `DBC_AUTHTOKEN`
  - Balance logging before each cost-incurring request
  - Affiliate link displayed when credits are empty
- **New API Endpoints** at `/dbc/api/`:
  - `GET /dbc/api/status/` - DBC status and balance
  - `GET /dbc/api/balance/` - Account balance
  - `GET /dbc/api/packages/` - Protected packages
  - `GET /dbc/api/jobs/` - Active captcha jobs
  - `POST /dbc/api/test_credentials/` - Test DBC credentials

### Removed
- **Sponsors_Helper Integration**: Completely removed

### Changed
- **Config**: New `[DBC]` section with encrypted credentials
- **Dispatcher**: New `DBCDispatcher`
- **Code Reorganization**: `kuasarr/providers/` restructured into submodules:
  - `captcha/` - DBC client, dispatcher, push jobs
  - `network/` - CF bypass, URL functions
  - `ui/` - HTML templates and images

---

## [1.3.0] - 2025-12-09

### Added
- **WX Source Integration**: New source for warez.cx
  - API-based link extraction with HTML fallback
  - Supports filecrypt.cc and hide.* links
  - Configure via `wx` hostname in config

### Removed
- **Manual Search** (`/search`): Web UI and API endpoints completely removed
- **Manual Link Intake** (`/manual-links`): Feature and related modules removed
  - Deleted files: `api/search.py`, `api/manual_links.py`, `downloads/manual_jobs.py`, `storage/manual_jobs.py`
- UI buttons "Manual Search" and "Manual Link Intake" removed from homepage

### Changed
- **DL Session**: Now uses username/password login instead of cookie files
  - More reliable as cookies don't expire
  - Cookie file fallback for backward compatibility
  - Configure via `[DL]` section with `user` and `password`
- **Link Extraction**: Simplified to only support filecrypt.cc and hide.*
  - Other link crypters/hosters log a warning
  - Reduces complexity and improves reliability
- `download()` function: Parameter `manual_job_id` removed
- Automatic search via Sonarr/Radarr remains fully functional
- **Homepage completely redesigned**:
  - New Kuasarr logo (512x512)
  - Modern action grid with emoji icons
  - Static file endpoint `/static/` for assets

---

## [1.2.2] - 2025-12-08

### Added
- **Hoster Blocking Feature**: New web UI at `/hosters` for blocking file hosters
  - 13 supported hosters: Rapidgator, DDownload, Nitroflare, Uploaded, Turbobit, Katfile, 1Fichier, FileFactory, MediaFire, MEGA, Keep2Share, Uptobox, Filer
  - API endpoints: `GET/POST /api/hosters/*`
  - Blocked links are automatically filtered from downloads

### Changed
- **Code Refactoring**: `shared_state.py` reduced from 998 to 204 lines
  - New modules: `jdownloader.py`, `hosters.py`, `validation.py`, `utils.py`, `magazine.py`
  - Backward compatibility maintained through re-exports
- **Real-Debrid Link**: Recommended premium link updated to `http://real-debrid.com/?id=13910652`

### Fixed
- **Config Fix**: New sections (Sonarr, Radarr, PostProcessing, BlockedHosters) are now correctly added without deleting existing entries

---

## [1.2.1] - 2025-12-08

### Fixed
- **Config Write Logic**: Adding new config sections no longer overwrites/deletes existing sections

---

## [1.2.0] - 2025-12-08

### Added
- **Post-Processing** for downloads
  - Automatic flattening of nested folder structures
  - Sonarr/Radarr rescan trigger via API
- **New Config Options**:
  - `[Sonarr]` with `url` and `api_key`
  - `[Radarr]` with `url` and `api_key`
  - `[PostProcessing]` with `flatten_nested_folders` and `trigger_rescan`

---
