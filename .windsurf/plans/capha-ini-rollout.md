om <!-- capha-ini-rollout 2025-11-18 -->

# CapHa.ini – Einführungsplan

> **Ziel:** CapHa erhält eine eigene `CapHa.ini` (analog zu `kuasarr.ini`) inklusive AES-verschlüsselter Secrets. Die Datei ersetzt die bisherige `.env`-basierte Konfiguration, behält jedoch alle CapHa-spezifischen Werte bei.


> **Umsetzungshinweis:** Markiere Fortschritte in diesem Plan (✅) und erweitere ihn bei neuen Anforderungen. Durch die detaillierte Beschreibung können weitere Chat-Agents sofort mitarbeiten.

## 0. Leitplanken & Annahmen

- Speicherort der neuen Datei: `captcha_helper/CapHa.ini`.
- Im Docker-Container muss `CapHa.ini` unter `/config/CapHa.ini` liegen; Ordner `/config` wird als Volume auf den Host gemountet, um Persistenz sicherzustellen.
- Verschlüsselung identisch zu Kuasarr (`kuasarr/storage/config.py`): AES-256-CBC, Key/IV aus `kuasarr.db` → Tabelle `secrets`.
- CapHa erhält eine eigene SQLite (`/config/CapHa.db`); dort werden Key/IV wie bei Kuasarr generiert und abgelegt.
- Secrets werden weiter über `secret|`-Präfix markiert. Nicht-Secret-Werte bleiben Klartext.
- Abschnitt `CapHa v2.0 Features` aus `.env.example` (Zeilen 14–18) bleibt unverschlüsselt.
- Die Pflege der Werte erfolgt manuell (kein automatisches Spiegeln aus `kuasarr.ini`).

## 1. Bestandsaufnahme & Vorbereitung

1. **Kuasarr-Verschlüsselung verstehen**  
   - Klassen `Config` & `DataBase` sichten (`kuasarr/storage/config.py`, `sqlite_database.py`).  
   - Notieren: Base64-kodierte `secret|`-Payload, Padding via `Cryptodome.Util.Padding.pad`.
2. **CapHa-Umgebung prüfen**  
   - Bestehende `.env`-Nutzung in `captcha_helper/service.py`, `docker-entrypoint.sh`, etc.  
   - Identifizieren, wo künftig INI gelesen werden muss.  
   - Prüfen, wo `/config` im Dockerfile/Compose gemountet wird und welche Pfade (INI, DB) dort liegen müssen.
3. **Werkzeugkette definieren**  
   - Option A: Re-Use Kuasarrs `Config`-Klasse via Helper-Script, das Werte entgegen nimmt und verschlüsselt.  
   - Option B: Eigenes CLI (`captcha_helper/tools/encrypt_ini.py`) mit kopiertem AES-Code.  
   - Entscheidung dokumentieren (Code-Sharing bevorzugt, um Doppelpflege zu vermeiden).

## 2. Struktur der CapHa.ini festlegen

1. **Sektionen übernehmen/teilen**  
   Vorschlag basierend auf `.env.example`:
   - `[CaptchaService]`: `DEATHBYCAPTCHA_TOKEN`, `NOX_USER`, `NOX_PASS` *(secret)*
   - `[KuasarrConnection]`: `KUASARR_URL` *(str)*, `KUASARR_API_KEY` *(secret)*, `MODE` *(str)*
   - `[Features]`: `CAPTCHA_MAX_CONCURRENT`, `CAPTCHA_TIMEOUT`, `CAPTCHA_DASHBOARD_ENABLED`, `CAPTCHA_PORT` *(alle Klartext, keine Verschlüsselung)*
   - `[Metadata]` (optional): `BUILD_DATE`, `VERSION`, `VCS_REF`, `LOG_LEVEL` falls weiterhin benötigt – Entscheidung treffen, ob diese zurückkehren.
2. **Mapping-Dokument erstellen**  
   - Tabelle „ENV → INI“ mit Typ (secret/str/bool).  
   - Klar definieren, welche Felder Pflicht/Optional sind.
3. **Defaults festlegen**  
   - Analog zu Kuasarr `Config._DEFAULT_CONFIG`: leere Strings für Secrets, sinnvolle Defaults für Bool/Int.  
   - Dokumentieren, wie boolsche Werte (`true`/`false`) serialisiert werden.

## 3. Verschlüsselungs-Workflow erarbeiten

1. **Key/IV-Verwaltung**  
   - CapHa generiert eigene Schlüsselpaare wie Kuasarr (AES-256-CBC).  
   - Key/IV in `/config/CapHa.db` (Tabelle `secrets`) speichern; falls DB fehlt → bei Start erzeugen.
2. **CLI/Helper bauen**  
   - Funktion `encrypt_value(value: str) -> str` implementieren (AES-256-CBC).  
   - Befehl `python captcha_helper/tools/encrypt_ini.py --section CaptchaService --key NOX_USER --value foo` erzeugt `secret|...`.
3. **INI-Schreibpfad**  
   - Script oder Management-Command, das komplette `CapHa.ini` aus einer Eingabequelle generiert (z. B. YAML/Prompt).  
   - Alternativ: Manuelles Editieren + CLI pro Wert dokumentieren.  
   - Sicherstellen, dass das Script standardmäßig nach `/config/CapHa.ini` schreibt (Pfad per ENV konfigurierbar).
4. **Dokumentation der Schritte**  
   - README-Abschnitt „CapHa.ini pflegen & Secrets verschlüsseln“ ergänzen.  
   - Beispiel: „1. Wert verschlüsseln → 2. `secret|...` in `CapHa.ini` eintragen → 3. Dienst neustarten“.

## 4. CapHa-Code anpassen

1. **INI-Lader schreiben**  
   - Modul `captcha_helper/config.py` erstellen, das ähnlich wie Kuasarr `Config`-Klasse arbeitet, aber nur CapHa-Sektionen kennt.  
   - Sicherstellen, dass `service.py` statt `.env` nun INI liest (z. B. via `configparser`).
2. **Rückwärtskompatibilität**  
   - Übergangsphase: `.env` weiterhin einlesen, falls `CapHa.ini` fehlt.  
   - Log-Warnung ausgeben, damit Nutzer migrieren.
3. **Secrets im Speicher**  
   - Nach Entschlüsselung sensible Werte nur im RAM halten; Logging vermeiden (bereits vorhanden via `ServiceLogger` + Masking).

## 5. Test & Validierung

1. **Unit-Tests**  
   - Tests für neue Config-Klasse: Schreiben, Lesen, Verschlüsseln/Entschlüsseln.  
   - Mock `DataBase('secrets')`, um Key/IV deterministisch zu halten.
2. **Integrationstest**  
   - Kompletten CapHa-Start mit `CapHa.ini` durchspielen.  
   - Prüfung: Kuasarr-API-Aufrufe erhalten `X-API-Key` aus INI.  
   - Validieren, dass `/config`-Volume korrekt befüllt wird (CapHa.ini + CapHa.db) und Container-Neustarts die Daten behalten.
3. **Regression**  
   - Docker-Einstieg (`docker-entrypoint.sh`) aktualisieren und testen (ENV → INI Konvertierung im Container?).
4. **Security-Check**  
   - Sicherstellen, dass `CapHa.ini` in `.gitignore` landet (falls nicht bereits).  
   - Dateirechte dokumentieren.

## 6. Rollout-Strategie

1. **Implementierungsreihenfolge**  
   1. ✅ Helper/CLI + Config-Layer.  
   2. ✅ Service-Refactor (`service.py` liest INI).  
   3. **Docker & Docs**.  
   4. QA + Release.  
   - Dockerfile/docker-compose ergänzen (`/config`-Volume, ENV für Pfade, Migrationshinweise).
2. **Kommunikation**  
   - Changelog-Eintrag + README-Update.  
   - Hinweis an alle Agenten: `.env` wird deprecated, `CapHa.ini` Pflicht ab Version X.
3. **Fallback**  
   - Bei Problemen: Feature-Flag `CAPHA_USE_ENV_FALLBACK=true` (nur Übergangsweise).  
   - Prozess dokumentieren, wie man wieder auf `.env` zurückstellt.

## 7. Offene Fragen / ToDos

- [ ] Teilen sich Kuasarr und CapHa denselben `kuasarr.db`-Pfad? Falls nein, wie werden Schlüssel synchronisiert?
- [ ] Sollen LOG-/BUILD-Metadaten wieder aufgenommen werden?  
- [ ] Benötigt CapHa zusätzliche Sektionen (Proxy, Parallelbetrieb, Dashboard-Auth)?
- [ ] Wie werden vorhandene `.env`-Installationen migriert (Script, Handbuch, automatischer Import)?


