---
description: Checkliste für Arbeitssessions am Captcha-Handler-Plan
---
1. Öffne den Plan `.cursor/plans/captcha-ce61b690.plan.md`, lies offene Aufgaben je Phase und verschaffe dir einen Überblick (bestehende ✅-Markierungen beachten).
2. Wähle die nächste Phase bzw. das konkrete Arbeitspaket aus dem Plan aus und formuliere das Session-Ziel (z. B. als Commit-/Issue-Notiz).
3. Bereite die Umgebung vor: aktiviere deine venv, starte benötigte Services/Container und stelle sicher, dass alle Secrets/ENV-Variablen gesetzt sind.
4. Setze das gewählte Arbeitspaket um: Code ändern, Tests schreiben/aktualisieren, manuelle Checks durchführen.
5. Führe passende Tests/Linter aus (z. B. `pytest`, `ruff`, manuelle Browser-Checks) und behebe Fehler.
6. Dokumentiere das Ergebnis: aktualisiere den Plan (✅ setzen, Statusnotiz ergänzen), passe README/Changelog bei Bedarf an und commite deine Änderungen.
