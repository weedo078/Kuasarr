---
description: Session-Checkliste für die Parallel-Pipeline
auto_execution_mode: 1
---

1. Plan `.windsurf/plans/Parallel-Pipeline.md` öffnen, aktuelle Phase und offene Tasks prüfen (✅-Status kontrollieren, bei Bedarf Statusnotiz ergänzen).
2. Session-Ziel definieren: konkrete Aufgabe/Phase auswählen und kurz notieren (Issue/Commit-Kommentar).
3. Voraussetzungen checken: venv aktivieren, Services/Container starten, Secrets und CapHa/Kuasarr-Endpoints konfigurieren.
4. Umsetzung: gewählte Aufgabe bearbeiten (Code/Config anpassen, Handshake-Logik, Queue, Monitoring etc. gemäß Plan).
5. Tests & manueller Check: relevante Unit-/Integrationstests ausführen, ggf. simulierte Mehrfach-Jobs testen.
6. Abschluss: Plan aktualisieren (✅ setzen, Statusblock ergänzen), Dokumentation/README anpassen,