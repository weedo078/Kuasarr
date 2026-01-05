---
description: Buildet weedo078/kuasarr Docker-Image nach Benutzer-Tag
auto_execution_mode: 1
---

1. Frage den Benutzer nach dem gewünschten Tag (z. B. `1.0.0`).
2. Stelle sicher, dass `docker buildx` verfügbar ist und ein Builder aktiv ist.
3. Führe (falls noch nicht passiert) `docker buildx create --name kuasarrbuilder --use` aus.
4. Führe (falls nötig) `docker buildx inspect --bootstrap` aus.
5. Führe `docker buildx build --platform linux/amd64,linux/arm64 -t "weedo078/kuasarr:<TAG>" --push .` aus.
6. Bestätige den Push und gib den Digest aus.
7. Frage den Benutzer, ob zusätzliche Tags (z. B. `latest`) gepusht werden sollen; falls ja, tagge/pushe den bereits gebauten Manifest-Index mit `docker buildx imagetools create -t "weedo078/kuasarr:<ZUSATZTAG>" "weedo078/kuasarr:<TAG>"` und gib den Digest aus.