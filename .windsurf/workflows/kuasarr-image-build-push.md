---
description: Buildet weedo078/kuasarr Docker-Image nach Benutzer-Tag
auto_execution_mode: 1
---

1. Frage den Benutzer nach dem gewünschten Tag (z. B. `1.0.0`).
2. Führe `   docker build -t "weedo078/kuasarr:<TAG> . ` aus.
3. Bestätige den erfolgreichen Build (Digest/Erfolgsmeldung notieren).
4. Führe `docker push weedo078/kuasarr:<TAG>` aus.
5. Bestätige den Push und gib den Digest aus.
6. Frage den Benutzer, ob zusätzliche Tags (z. B. `latest`) gepusht werden sollen; falls ja, wiederhole Schritte 2–5 mit diesen Tags.