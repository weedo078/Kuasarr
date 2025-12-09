---
description: Build hardened CapHa Docker image with Nuitka multi-stage pipeline
---
1. Voraussetzungen
   - Stelle sicher, dass `python:3.11-slim` (oder gewünschte Version) als Basisimage verfügbar ist.
   - Systempakete, die Nuitka benötigt: `gcc`, `g++`, `make`, `libffi-dev`, `libssl-dev` (abhängig vom Projekt ggf. mehr).
   - Projektdateien enthalten `requirements.txt` und den Einstiegspunkt (z. B. `service.py`).

2. Builder-Stage vorbereiten
   1. Starte ein Multi-Stage-Dockerfile mit `FROM python:3.11-slim AS builder`.
   2. Installiere Systemtools: `apt-get update && apt-get install -y gcc g++ make` (+ weitere Abhängigkeiten).
   3. Setze `WORKDIR /app` und kopiere `requirements.txt` hinein.
   4. Installiere Dependencies + Nuitka: `pip install -r requirements.txt nuitka`.
   5. Kopiere den restlichen Projektcode in `/app` (`COPY . .`).
   6. Führe Nuitka aus, z. B.:
      ```
      nuitka --standalone --onefile --enable-plugin=pkg-resources \
             --output-filename=capha_bin service.py
      ```
      - Passe Plugins (z. B. `multiprocessing`, `tk-inter`) bei Bedarf an.
      - Verwende `--include-data-files`, falls zusätzliche Assets benötigt werden.

3. Runtime-Stage erstellen
   1. Wechsle zu einer schlanken Basis, z. B. `FROM debian:bookworm-slim` (alternativ distroless, Alpine nur wenn Bibliotheken kompatibel sind).
   2. Setze erneut `WORKDIR /app`.
   3. Kopiere nur das gebaute Binary + benötigte Shared Objects:
      ```
      COPY --from=builder /app/capha_bin /app/capha
      COPY --from=builder /app/capha_bin.dist /app/capha.dist
      ```
      (bei `--onefile` genügt das einzelne Binärfile; bei `--standalone` zusätzlich der dist-Ordner).
   4. Füge nur unbedingt notwendige Systemlibs hinzu (z. B. `apt-get install -y libstdc++6`), dann `apt-get clean && rm -rf /var/lib/apt/lists/*`.
   5. Nicht benötigte Shell-Tools entfernen oder das Dateisystem read-only mounten (optional).
   6. Setze einen nicht privilegierten Benutzer (`useradd -m appuser`, `USER appuser`).
   7. Definiere den EntryPoint: `ENTRYPOINT ["/app/capha"]`.

4. Tests & Verifikation
   - Lokaler Build: `docker build -t kuasarr/capha:nuitka .`
   - Container starten und Funktionstest ausführen (`docker run --rm kuasarr/capha:nuitka --help`).
   - Prüfen, ob nur das Binary im Image liegt (`docker run --rm ... ls /app`).

5. Sicherheit & Deployment
   - Optional: Binary signieren oder Hash prüfen, bevor es in die Runtime-Stage kopiert wird.
   - Sensible ENV-Variablen nur zur Laufzeit setzen (nicht im Image bake'n).
   - Bei Updates: Builder-Stage erneut durchlaufen lassen; der Runtime-Stage-Abschnitt bleibt unverändert.


beispiel:1
FROM python:3.11-slim AS builder
RUN apt-get update && apt-get install -y gcc g++ make
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt nuitka
COPY . .
RUN nuitka --standalone --onefile --enable-plugin=pylint-warnings \
           --output-filename=capha service.py

FROM debian:bookworm-slim
WORKDIR /app
COPY --from=builder /app/capha /app/capha
ENTRYPOINT ["/app/capha"]