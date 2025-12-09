---
description: Entfernen der Features "Manuelle Suche" und "Manual Link Intake" aus Kuasarr
---
1. Kontext
   - Aktuell existieren zwei eigenständige UI-Bereiche in Bottle:
     1. `/search` (Manuelle Suche) inkl. API-Endpunkte in `kuasarr/api/search.py`
     2. `/manual-links` (Manual Link Intake) in `kuasarr/api/manual_links.py`
   - Beide nutzen Template-Hilfen (`html_templates`), DB-Zugriff (`shared_state.get_db`) und Download-Pipelines.
   - Ziel: Funktionen vollständig entfernen, inklusive REST-Endpunkte, Routen, UI-Buttons, Templates und eventueller Konfigurationen.

2. Vorbereitung / Analyse
   1. Erfasse sämtliche Einstiege:
      - Routen in `kuasarr/api/__init__.py` (Buttons, Imports)
      - direkte Aufrufe aus Frontend (JS, Buttons auf `/` Startseite)
      - Cron/CLI-Aufrufe (falls vorhanden über `providers/shared_state`, `downloads/manual_jobs.py` etc.)
   2. Suche nach Bezeichnern wie `manual`, `Manuelle Suche`, `Manual Link Intake` im Repo (`grep "manual-links"`, `grep "manual link"`).
   3. Prüfe Datenbank-Tabellen (`manual_links`, `manual_jobs`?) und Config-Sektionen.

3. Entfernungsschritte
   1. API/Routes
      - Entferne `setup_search_routes()` und `setup_manual_link_routes()` Aufrufe in `kuasarr/api/__init__.py`.
      - Lösche (oder archiviere) `kuasarr/api/search.py` und `kuasarr/api/manual_links.py`.
      - Entferne alle Verweise auf diese Module.
   2. UI
      - Entferne Buttons/Links auf der Startseite (`index()` in `api/__init__.py`).
      - Entferne statische Assets/JS, die ausschließlich dafür genutzt wurden.
   3. Backend
      - Entferne Hilfsfunktionen aus `downloads/manual_jobs.py`, `downloads/packages/__init__.py`, `search/*` sofern nur für manuelle Suche.
      - Prüfe `providers/shared_state` auf Flags/Stati (`recently_searched`, `manual_links_db`).
      - Entferne DB-Tabellen/Seeder (z. B. `manual_links`, `manual_jobs`). Optional: Migration/Upgrade-Skript, das Tabellen löscht.
   4. Konfiguration
      - Entferne CLI-Flags, Config-Sektionen oder ENV-Variablen, die ausschließlich für diese Features existieren.
      - Aktualisiere `README.md` und evtl. `docs/PARALLEL_MODE_GUIDE.md`.

4. Tests / Validierung
   1. `python -m py_compile` für betroffene Module.
   2. Integrationstest: `venv` → `python -m kuasarr` starten, Home-Page prüfen (Buttons weg, keine 404s).
   3. Funktionstest Download-Pipeline (z. B. per CLI Trigger) sicherstellen, dass automatische Suche weiterhin funktioniert.

5. Kommunikation
   - `CHANGELOG.md` Eintrag (Removed: Manual Search & Manual Link Intake).
   - Versionsnummer anpassen (z. B. `version.json`).
   - Release-Notes / PR-Beschreibung anlegen.
