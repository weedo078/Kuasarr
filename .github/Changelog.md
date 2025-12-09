# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

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
