---
description: Anleitung, um Updates aus dem offiziellen Quasarr-Repository in den Kuasarr-Fork einzupflegen, Merge-Konflikte zu lösen und den Code anschließend zu integrieren.
auto_execution_mode: 1
---

## Voraussetzungen

1. Git-Status prüfen und sicherstellen, dass keine uncommitteten Änderungen offen sind:
   ```powershell
   git status --short
   ```
   - Falls Änderungen vorhanden sind: committen oder mit `git stash push` sichern.
2. Projekt-Root (`Kuasarr\`) in einer PowerShell öffnen.
3. Remotes prüfen, um sicherzustellen, dass `origin` auf **weedo078/kuasarr** und `upstream` auf **rix1337/quasarr** zeigt:
   ```powershell
   git remote -v
   ```
   Erwartete Standard-URLs:
   - `origin  https://github.com/weedo078/kuasarr.git`
   - `upstream  https://github.com/rix1337/Quasarr.git`
   Falls eine URL abweicht, entsprechend anpassen. Falls `upstream` fehlt, hinzufügen:
   ```powershell
   git remote add upstream https://github.com/rix1337/Quasarr.git
   ```
   (Adresse bei Bedarf anpassen.)

## Update abrufen & Arbeitsbranch erstellen

1. Neueste Stände holen (origin = Kuasarr-Fork, upstream = Quasarr-Quelle):
   ```powershell
   git fetch origin
   git fetch upstream
   ```
2. Lokalen Hauptbranch aktualisieren:
   ```powershell
   git checkout main
   git pull --ff-only origin main
   ```
3. Arbeitsbranch für das Update anlegen:
   ```powershell
   $branchName = "chore/update-quasarr-$(Get-Date -Format 'yyyyMMdd')"
   git checkout -b $branchName
   ```

## Neue Version bereitstellen

1. Verfügbare neue Version identifizieren (z. B. per Release Notes oder `git tag -l --sort=-version:refname`).
2. Zielpfad definieren und ggf. anlegen:
   ```powershell
   $version = "<neue-version>"
   $target = "C:\Users\gianj\Cursor Projekte\Quasarr\Quasarr\Quasarr\$version"
   if (-not (Test-Path $target)) { New-Item -ItemType Directory -Path $target | Out-Null }
   ```
3. Quasarr-Quellstand in den Zielordner kopieren (Pfad zur Quelle bei Bedarf anpassen, z. B. ausgecheckter `upstream/main`-Stand):
   ```powershell
   Copy-Item -Path ".\Quasarr" -Destination $target -Recurse -Force
   ```
4. Prüfen, dass die neue Version vollständig kopiert wurde (`Get-ChildItem $target | Format-Table`).

## Neue Funktionen prüfen & Integration abstimmen

1. Änderungen und neue Funktionen der Version zusammentragen (Release Notes, `git log upstream/main --oneline`, Diff-Auswertung).
2. Stichpunktliste der neuen Funktionen erstellen (z. B. `notes/new_features_<version>.md`).
3. Liste mit dem Projektverantwortlichen besprechen (z. B. Übergabe an diesen Chat) und gemeinsam entscheiden, welche Features in Kuasarr integriert werden.
4. Nur freigegebene Funktionen/Änderungen im weiteren Verlauf übernehmen.

## Upstream-Änderungen mergen

1. Offizielle Änderungen (Quasarr → Kuasarr) einspielen:
   ```powershell
   git merge upstream/main
   ```
2. Wenn der Merge ohne Konflikte durchläuft, direkt mit Abschnitt **Codeübernahme & Tests** fortfahren.

## Merge-Konflikte identifizieren & lösen

1. Konflikte anzeigen:
   ```powershell
   git status --short
   git diff --name-only --diff-filter=U
   ```
2. Jede betroffene Datei öffnen, Konfliktmarker (`<<<<<<<`, `=======`, `>>>>>>>`) auflösen und die gewünschte Logik sauber zusammenführen.
   - Für strukturierte Vergleiche kann optional ein Tool genutzt werden (z. B. `code --diff`, `meld`, `git mergetool`).
3. Nach der Bereinigung jede Datei markieren:
   ```powershell
   git add <pfad/zur/datei>
   ```
4. Prüfen, ob weitere Konflikte bestehen. Falls ja, Schritte 1–3 wiederholen.
5. Merge abschließen:
   ```powershell
   git commit --no-edit
   ```
   (Bei manuellen Anpassungen Commit-Message nach Bedarf ergänzen.)

## Codeübernahme & Tests

1. Projekt-spezifische Anpassungen (z. B. in `captcha_helper` oder eigenen Erweiterungen) in den neuen Stand integrieren.
2. Sicherstellen, dass alle Imports und Konfigurationen weiterhin stimmen.
3. Automatisierte Checks laufen lassen:
   ```powershell
   pytest
   ```
   oder zielgerichtete Kommandos je nach Projekt (Linting, Integrationstests).
4. Optional: Docker-Setup prüfen
   ```powershell
   docker compose -f docker/dev-services-compose.yml up captcha-helper
   ```
   und sicherstellen, dass die Dienste starten.

## Abschluss

1. Überblick über Änderungen verschaffen:
   ```powershell
   git status
   git diff --stat origin/main
   ```
2. Commit-Message ergänzen, falls noch nicht geschehen, und Branch pushen:
   ```powershell
   git push origin $branchName
   ```
3. Pull Request gegen `main` erstellen und Reviewer informieren.
4. Offene Stashes oder temporäre Branches nach erfolgreicher Integration bereinigen.
