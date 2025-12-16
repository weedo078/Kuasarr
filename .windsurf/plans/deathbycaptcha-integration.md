# DeathByCaptcha-Integration für Kuasarr

## 1. Ausgangslage & Zielsetzung
- Kuasarr nutzt aktuell ausschließlich CaptchaSolverr (Push-Dispatcher, Callback-API).
- DeathByCaptcha (DBC) soll CaptchaSolverr vollständig ersetzen.
- Vorgaben:
  - Alle Captcha-Lösungen laufen nur noch über DBC.
  - Standard-Timeouts/-Retries sind ausreichend.
  - Vor **jedem** kostenpflichtigen Request DBC-Kontostand loggen; bei 0 Credits Affiliate-Link `https://deathbycaptcha.com?refid=1237432788a` ausgeben.
  - Credentials müssen verschlüsselt in `kuasarr.ini` gespeichert werden.
  - Referenzen liegen unter `.reference/solvers` (insbes. `deathbycaptcha.py`).

## 2. Architekturübersicht
1. **Config & Secrets**
   - Neue Sektion `DeathByCaptcha` in `kuasarr.ini` (`encrypted_username`, `encrypted_password` oder `encrypted_api_token`, optional `host`, `timeout`, `max_retries`, `retry_backoff`).
   - ENV-Overrides: `DBC_USERNAME`, `DBC_PASSWORD`, `DBC_API_TOKEN`, `DBC_HOST`, ...
   - Web-UI Input + „Test Balance“-Button.

2. **Shared State**
   - Beim Start: CaptchaSolverr-Konfiguration entfernen, DBC-Credentials entschlüsseln und in `shared_state` hinterlegen (`dbc_credentials`, `dbc_settings`).
   - Flags/Keys neutralisieren (z. B. `helper_active` → `captcha_provider_active`).

3. **Client-Modul**
   - `kuasarr/providers/deathbycaptcha_client.py` (Basis: `.reference/solvers/deathbycaptcha.py`).
   - Funktionen: `get_balance()`, `decode(captcha_type, payload)`, `report(captcha_id)`, Fehlerklassen.
   - Balance-Logging & Affiliate-Link bei 0 Credits zentral implementieren.

4. **Dispatcher & Workflow**
   - Neuer `DBCDispatcher` ersetzt CaptchaSolverr-Push-Dispatcher.
   - Ablauf pro Paket:
     1. `protected`-Eintrag laden und Crypter-Fluss starten (bestehende Linkdecrypt-/Session-Module nutzen).
     2. Captcha-Challenge extrahieren → an DBC senden → Lösung einsetzen → HTTP-Fluss fortführen, bis Download-Links vorliegen.
     3. Links an `shared_state.download_package()` übergeben; bei Fehler Retry/Fail gemäß `max_attempts`.
   - Polling statt Callback (DBC liefert Captcha-ID).

5. **API & Monitoring**
   - `/captchasolverr/api/*` Endpoints entfernen oder zu `/dbc/api/*` migrieren.
   - Status-Route liefert DBC-Balance, offene Jobs, Queue-Infos.
   - Discord/Notification-Texte anpassen (Provider-Name, Balance-Warnung).

## 3. Umsetzungsschritte
1. **Aufräumen CaptchaSolverr**
   - Entferne Client, Dispatcher, API-Endpunkte, Config-Einträge.
   - Migration: alte Config-Werte ignorieren oder „deprecated“-Hinweis loggen.

2. **Config & Encryption**
   - `storage/config.py`: neue `DeathByCaptcha`-Sektion, Secrets als verschlüsselte Felder.
   - UI + CLI + Docker-Doku anpassen.

3. **Cliententwicklung**
   - HTTP-/Socket-Client nach Vorgabe implementieren.
   - Einheitliche Exception-Hierarchie (`DBCError`, `DBCServiceOverload`, ...).
   - Balance-Logging in Client-Wrapper.

4. **Dispatcher/Worker**
   - Neues Modul `providers/dbc_dispatcher.py` mit Loop, Backoff, `push_jobs`-Integration.
   - Anpassung `push_jobs`: keine Remote-Job-IDs/Callbacks nötig, aber Retry-Zähler behalten.

5. **Link-Decryption-Flow**
   - Überprüfe vorhandene Crypter-/Hoster-Handler (`kuasarr/providers/sessions`, `downloads/linkcrypters`, etc.).
   - Ergänze Hilfsfunktionen zur Captcha-Extraktion (HTML, Bilder) und Formular-Submission.
   - Stelle sicher, dass alle Kuasarr-relevanten Mirror unterstützt werden.

6. **Logging & Monitoring**
   - Jeder kostenpflichtige DBC-Call → Balance-Logeintrag.
   - Bei Balance ≤ 0 → zusätzlicher Logeintrag mit Affiliate-Link.
   - StatsHelper um DBC-spezifische Metriken erweitern (success/fail, credits used).

7. **Dokumentation & Tests**
   - README, CHANGELOG, Docker-Hub-Beschreibung aktualisieren.
   - Beispiel `kuasarr.ini` + ENV Variablen.
   - Tests: Unit (Client), Integration (Mock-DBC), manuell via Sonarr/Radarr + echtem DBC-Account.

## 4. Risikobewertung & Mitigation
- **Crypter-Flow-Komplexität**: ggf. zusätzliche HTML-Parsing-Logik nötig → frühzeitig PoC mit Haupt-Cryptern.
- **DBC-Limits/Kosten**: Log-Warnung + Affiliate-Link, optional Soft-Stop bei Balance < X.
- **Credential-Sicherheit**: sicherstellen, dass bestehende Verschlüsselung robust genug ist; Master-Key über ENV.

## 5. Abhängigkeiten & Ressourcen
- Referenzimplementierungen in `.reference/solvers` (insb. `deathbycaptcha.py`).
- Vorhandene Crypter-/Download-Module (`kuasarr/downloads`, `kuasarr/providers/sessions`).
- DBC-Account des Users für Tests.

## 6. Implementierungsstatus

### ✅ Abgeschlossen (2025-12-09)

1. **Config & Encryption** ✅
   - `storage/config.py`: Neue `[DeathByCaptcha]`-Sektion mit verschlüsselten Credentials
   - ENV-Overrides: `DBC_USERNAME`, `DBC_PASSWORD`, `DBC_AUTHTOKEN`, `DBC_TIMEOUT`, etc.

2. **DBC-Client** ✅
   - `kuasarr/providers/deathbycaptcha_client.py` (570+ Zeilen)
   - HTTP API Client mit Retry-Logik
   - Methoden: `get_balance()`, `solve_captcha()`, `solve_recaptcha_v2()`, `solve_cutcaptcha()`, `report_incorrect()`
   - Exception-Hierarchie: `DBCError`, `DBCAccessDenied`, `DBCServiceOverload`, `DBCInsufficientCredits`
   - Balance-Logging vor jedem kostenpflichtigen Request
   - Affiliate-Link bei 0 Credits: `https://deathbycaptcha.com?refid=1237432788a`

3. **DBC-Dispatcher** ✅
   - `kuasarr/providers/dbc_dispatcher.py` (500+ Zeilen)
   - Background-Thread für automatische Captcha-Lösung
   - Unterstützt: Filecrypt (CutCaptcha, reCAPTCHA, Image), Nox (reCAPTCHA), generische Image-Captchas
   - Retry-Logik mit Backoff
   - Integration mit `push_jobs` und `shared_state`

4. **API-Endpoints** ✅
   - `kuasarr/api/dbc/__init__.py` (280+ Zeilen)
   - `GET /dbc/api/status/` - Status und Balance
   - `GET /dbc/api/balance/` - Kontostand
   - `GET /dbc/api/packages/` - Geschützte Pakete
   - `GET /dbc/api/jobs/` - Aktive Jobs
   - `POST /dbc/api/test_credentials/` - Credentials testen
   - Legacy-Redirect: `/captchasolverr/api/status/` → DBC

5. **Initialisierung** ✅
   - `kuasarr/__init__.py` angepasst
   - CaptchaSolverr-Code ersetzt durch DBC
   - `DBCDispatcher` wird bei Startup gestartet

6. **Dokumentation** ✅
   - README.md aktualisiert mit DBC-Konfiguration
   - CHANGELOG.md: Version 1.4.0 mit DBC-Integration

### 🔜 Ausstehend

- Manuelle Tests mit echtem DBC-Account via Sonarr/Radarr
- Web-UI für DBC-Konfiguration (optional)
- Erweiterte Crypter-Unterstützung (falls nötig)
