---
description: Anleitung, wie nach einem Update des fremden „SponsorsHelper“-Codes der neue Stand per Docker-Image in das lokale Projekt geholt und anschließend legal refaktoriert wird.
auto_execution_mode: 1
---

## Voraussetzungen

1. Docker Desktop starten und sicherstellen, dass der Status **Running** ist.
2. Falls noch nicht geschehen, einmalig am Container-Registry-Host anmelden:
   ```powershell
   docker login ghcr.io
   ```
3. SponsorsHelper-Image aktualisieren:
   ```powershell
   docker pull ghcr.io/rix1337-sponsors/docker/helper:latest
   ```
4. Prüfen, dass folgende Umgebungsvariablen für den späteren Betrieb gesetzt sind (z. B. per `.env` oder temporär in der Session): `DEATHBYCAPTCHA_TOKEN`, `NOX_USER`, `NOX_PASS`, `KUASARR_URL`, `CAPTCHA_PORT`. Optional: `FLARESOLVERR_URL`.

## Export des aktuellen SponsorsHelper-Codes

1. PowerShell im Projekt-Root `Quasarr\` öffnen.
2. Exportskript mit vordefinierten Parametern ausführen:
   ```powershell
   $image = 'ghcr.io/rix1337-sponsors/docker/helper:latest'
   $sourcePath = '/rix'
   powershell -ExecutionPolicy Bypass -File .\extract-helper-image.ps1 -Image $image -SourcePath $sourcePath
   ```
3. Nach erfolgreichem Lauf liegt der entpackte Code unter `captcha_helper\neue_version_<Zeitstempel>\rix`.

## Vergleich & Refaktorierung

1. Die neue `rix`-Struktur mit den bestehenden Referenzen (`captcha_helper\*`, bestehende Module) vergleichen.
2. Relevante Module (u. a. `captcha_helper\service.py`, `captcha_helper\captcha_handler.py`, Dateien unter `captcha_helper\captchas\`) schrittweise übernehmen:
   - Jeden Abschnitt juristisch sauber neu formulieren (keine Copy-Paste 1:1).
   - Abhängigkeiten/Imports direkt im Zielmodul anpassen.
3. Nicht benötigte Dateien der neuen Version dokumentiert verwerfen (z. B. im Commit-Message festhalten).

## Funktionsprüfung

1. Nach jeder größeren Übernahme `pytest captcha_helper` (oder vorhandene Tests/Linter) ausführen.
2. Sicherstellen, dass Docker-abhängige Komponenten weiter starten.
3. Änderungen committen und Pull Request erstellen.