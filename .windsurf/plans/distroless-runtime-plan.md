# Plan: Distroless Runtime Container mit Nuitka-Binaries

## 1. Hintergrund & Ziel
- Aktuell: `captcha_helper/docker/Dockerfile` nutzt 2 Stages (Python 3.11 slim Builder, Debian slim Runtime) und kopiert Nuitka-Onefile-Binaries + Hilfsskripte (`dashboard.html`, `simple_monitoring.py`, etc.).
- Wunsch: Runtime-Image mit **distroless**-Basis, das nur die gestrippten Nuitka-Binaries + benötigte Konfig-/Hilfsdateien enthält, um Image-Größe und Angriffsfläche zu reduzieren.
- Schutzbedingung: Nuitka-Compilation bleibt bestehen, damit der Python-Code nicht offenliegt.

## 2. Voraussetzungen
1. Docker BuildKit aktiviert (empfohlen via `DOCKER_BUILDKIT=1`).
2. Zugriff auf `gcr.io/distroless` Images (ggf. `docker pull gcr.io/distroless/base-debian12`).
3. Nuitka >= 2.2 bereits im Builder installiert (siehe `captcha_helper/requirements.txt`).
4. Möglichkeit, native Abhängigkeiten der erzeugten Binaries zu prüfen (`ldd`).

## 3. High-Level-Schritte
1. **Builder-Stage optimieren** (Binaries strippen/komprimieren, Artefakte vorbereiten).
2. **Benötigte Runtime-Libs ermitteln** (ldd auf Binaries, Liste pflegen).
3. **Distroless Runtime-Stage erstellen** (passendes distroless Image wählen, Files kopieren, fehlende libs injizieren).
4. **Entrypoint/Startskripte anpassen** (wegen fehlender Shell in distroless).
5. **Testen & Validieren** (lokaler Lauf, minimaler Smoke-Test, Image-Größe vergleichen).

## 4. Detailplan

### Schritt 1 – Builder-Stage anpassen
- **Basis belassen** (`python:3.11-slim-bookworm`) oder weiter abspecken (optional) – wichtig ist saubere Trennung.
- Nach jedem Nuitka-Build folgende Optimierungen ergänzen:
  ```dockerfile
  RUN strip /build/output/captcha_handler || true \
      && strip /build/output/captcha_service || true \
      && strip /build/output/capha_config_cli || true
  ```
- Optional UPX-Kompression (nur wenn Lizenz & Stabilität ok): `upx --best --lzma /build/output/captcha_* /build/output/capha_config_cli`.
- Sicherstellen, dass sämtliche Hilfsdateien, die im Runtime-Image benötigt werden, in einem dedizierten Directory landen (z. B. `/build/runtime_payload`).

### Schritt 2 – Runtime-Abhängigkeiten erfassen
- Innerhalb des Builder-Containers (nach der Compilation):
  ```bash
  ldd /build/output/captcha_handler
  ldd /build/output/captcha_service
  ldd /build/output/capha_config_cli
  ```
- Liste aller benötigten Shared Libraries erfassen (typisch: `libc`, `libdl`, `libpthread`, `libm`, `librt`, `libstdc++`, `libgcc_s`, evtl. `libz`, `libssl`, `libcrypto`).
- Prüfen, ob zusätzliche Dateien (z. B. CA-Zertifikate für HTTPS-Calls) erforderlich sind.

### Schritt 3 – Distroless Runtime-Stage bauen
1. **Image auswählen**:
   - Startpunkt `gcr.io/distroless/cc-debian12` (enthält glibc + CA-Zertifikate + nonroot user).
   - Falls Python-Skripte weiter gebraucht werden (z. B. `simple_monitoring.py`), entweder:
     - in Nuitka-Binary umwandeln, oder
     - distroless `python3-debian12` verwenden (größer) oder BusyBox-Ersatz organisieren.
   - Ziel: Keine interpretierten Skripte → alles kompiliert oder als Go/Node-Binär.
2. **Dateien kopieren**:
   - `COPY --from=builder /build/output/ /app/bin/`
   - Weitere Assets (`dashboard.html`, Config-Templates) falls zwingend nötig.
   - Keine Shellskripte verwenden; wenn EntryLogic erforderlich ist, kleines statisches Binary bauen oder vorhandenen Handler erweitern.
3. **Libs injizieren**:
   - Fehlende `.so` Files aus Builder holen: `COPY --from=builder /usr/lib/x86_64-linux-gnu/libssl.so.3 /usr/lib/x86_64-linux-gnu/`
   - Nur die konkret benötigten Bibliotheken übernehmen.
4. **User & Permissions**:
   - Distroless nutzt `nonroot`. Falls anderer User nötig: `USER nonroot:nonroot` oder eigenen UID/GID via `USER 65532:65532`.
5. **Entrypoint**:
   - Beispiel: `ENTRYPOINT ["/app/bin/captcha_service"]`
   - Wenn mehrere Prozesse (Service + Handler) nötig sind, Supervisor-Ansatz über zusätzlichen Binärstarter (`launcher`) oder `tini`-ähnliches statisches Binary.

### Schritt 4 – Hilfs- & Configdateien
- Prüfen, welche Dateien im aktuellen Runtime-Image verbleiben müssen:
  - `docker-entrypoint.sh` ➜ ersetzen durch in Go/Python (Nuitka) kompilierten Starter.
  - `dashboard.html` ➜ falls weiterhin ausgeliefert wird, als statisches Asset behalten.
  - `simple_monitoring.py`, `request_tracker.py` ➜ entweder in bestehende Binaries integrieren oder ebenfalls via Nuitka kompilieren.
- Volume-/Env-Definitionen beibehalten, aber Pfade ggf. anpassen (`/app/bin`).

### Schritt 5 – Tests & Validierung
1. Lokales Build: `docker build -f captcha_helper/docker/Dockerfile -t capha:distroless .`
2. Container testen (Parameter/ENV wie bisher):
   ```bash
   docker run --rm -p 9700:9700 -v %cd%/config:/config capha:distroless
   ```
3. Smoke-Test: Healthcheck, Zugriff auf Dashboard, CAPTCHA-Workflow.
4. Größe vergleichen: `docker images capha:distroless capha:current`.
5. Sicherheitscheck: `docker scout cves capha:distroless` (optional).

### Schritt 6 – Rollout / Backout
- **Rollout**: Taggen (`capha:distroless`, `:latest`), Push zu Registry, Compose-/Helm-Definitionen aktualisieren.
- **Backout**: Vorherige Debian-slim Runtime als Fallback-Tag behalten (`capha:legacy`).

## 5. Offene Punkte / Entscheidungen
1. Brauchen wir weiterhin Shell/Monitoring-Skripte? → Falls ja, geeignete Alternative definieren.
2. Welche distroless-Variante ist final (cc vs. base vs. static)?
3. Akzeptanz von UPX-Kompression? → Performance-Tests nötig.
4. Müssen zusätzliche CA-Zertifikate oder Fonts für Captcha-Verarbeitung vorhanden sein?

## 6. Akzeptanzkriterien
- Docker-Image basiert auf distroless.
- Alle notwendigen Komponenten (Service, Handler, Config-CLI) laufen ohne Interpreter.
- Kein Bash/Shell im Runtime-Image.
- Funktionale Parität zu aktuellem Build (CAPTCHA lösen, Dashboard, Healthchecks).
- Messbare Größenreduktion (Ziel < 200 MB, konkret festzulegen).
