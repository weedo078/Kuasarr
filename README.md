# Quasarr (DL‑Integration Fork)

Diese Fork‑Variante ergänzt Quasarr um:

- DL‑Integration: erweiterter Download‑Flow inkl. Zielordner‑Unterstützung (destination_folder)
- Direkte‑Link‑Funktion (Manual Link Intake) über eigene API/UI‑Route

Für Funktionsumfang, Einrichtung und alle Details verweise ich auf die Original‑Dokumentation: [Original README von rix1337](https://github.com/rix1337/Quasarr#readme)

## Image

Docker Hub: [weedo078/quasarr-dl](https://hub.docker.com/r/weedo078/quasarr-dl)

Beispiel:

```bash
docker run -d \
  --name="quasarr-dl" \
  -p 8080:8080 \
  -v /path/to/config/:/config:rw \
  -e 'INTERNAL_ADDRESS'='http://192.168.0.1:8080' \
  -e 'EXTERNAL_ADDRESS'='http://192.168.0.1:8080' \
  weedo078/quasarr-dl:latest
```

Tags:
- `latest`
- `v1.16.5-dl.1`
(siehe [Tags-Übersicht](https://hub.docker.com/r/weedo078/quasarr-dl/tags))

Hinweis: Hostname‑Konfiguration, JDownloader‑Anbindung, Radarr/Sonarr‑Setup etc. erfolgen wie im Original beschrieben (siehe Link oben).

## Lizenz und Attribution

- Lizenz: MIT (siehe `LICENSE` in diesem Repository)
- Copyright (c) 2024 RiX
- Dieses Projekt ist ein Fork von `rix1337/Quasarr` — Quelle und vollständige Anleitung: [https://github.com/rix1337/Quasarr](https://github.com/rix1337/Quasarr)
