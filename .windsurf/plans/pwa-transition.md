# Kuasarr Web-UI → Progressive Web App (PWA) Plan

## Ziele & Randbedingungen
- Installierbare Web-App (Manifest + Service Worker) ohne Feature-Regressions.
- Performance/WARP: Keine Verlangsamung von Kuasarr; Service Worker muss Requests nicht verzögern.
- Offline- bzw. Low-Connectivity-Unterstützung für statische UI, nicht zwingend für API.
- Sichere Bereitstellung (HTTPS, korrekte Caching-Strategien, Fallback-Handling).
- Minimaler Eingriff in bestehende Backend-Performance.

## Architektur-Übersicht
1. **Manifest + Assets**
   - Neues `manifest.webmanifest` unter `kuasarr/static/` mit Logos (192, 512 px, ggf. Maskable).
   - Theme-/Background-Color, `display: standalone`, `start_url: /`.
   - Verlinkung im HTML (`<link rel="manifest" href="/static/manifest.webmanifest">`).
2. **Service Worker**
   - Datei `kuasarr/static/sw.js`; Registrierung in UI (z.B. `static/js/app.js`).
   - Rollen: Precache statische Assets, optional API-Fallback (Network-first).
   - Performance: SW soll API-Calls nur proxyen, wenn nötig; ansonsten `self.skipWaiting()`/`clients.claim()`.
3. **Build-/Serve-Pipeline**
   - Jinja/Bottle Templates erweitern, um Manifest & SW einzubinden.
   - Deployment (Docker, EXE, PyPI) liefert Manifest + SW + Icons.
4. **QA/Monitoring**
   - Lighthouse Audit (PWA/Performance/Best Practices).
   - Browser-Tests (Chrome/Edge/Firefox) + Mobil (Android A2HS).
   - Regression-Tests: Page load time, API throughput.

## Work Breakdown Structure

### Phase 1 – Grundlagen (1–2 Tage)
1. **Asset-Inventar**
   - Liste aller statischen Dateien & kritischen API-Endpunkte erstellen.
   - Prüfen, welche Assets precached werden dürfen vs. dynamische Endpunkte.
2. **Manifest vorbereiten**
   - Icons generieren (SVG → PNG 512/256/192/128/96/72/48).
   - Festlegen: Name, Short name, Description, Theme/Background Colors.
   - `manifest.webmanifest` + `<meta name="theme-color">`.
3. **HTML-Anpassungen**
   - Manifest-Link + `apple-touch-icon`, `mask-icon` (Safari) hinzufügen.
   - `<meta name="viewport">` prüfen.

### Phase 2 – Service Worker & Caching (2–3 Tage)
1. **SW Grundgerüst**
   - Registrierungscode (`navigator.serviceWorker.register('/static/sw.js')`).
   - Versionierung via `CACHE_NAME = 'kuasarr-static-v1'`.
2. **Precache & Runtime Caching**
   - Precache: CSS, JS, Logo, Manifest.
   - Runtime (Network-first) für `/api/*` → verhindert veraltete Daten.
   - Offline-Fallback (HTML-Shell + Hinweis);
   - Performance-Schutz: API-Requests nicht doppelt cachen; Response passthrough bei großen Payloads.
3. **Update-Mechanik**
   - `self.skipWaiting()` & `clients.claim()` nach Activation.
   - UI-Hinweis „Neue Version verfügbar“ (optionale spätere Iteration).
4. **Config**
   - Environment Flag zum Deaktivieren des SW (z.B. `PWA_ENABLED`).

### Phase 3 – Sicherheit & Deployment (1 Tag)
1. **HTTPS-Anforderungen**
   - Dokumentation für Nutzer (Reverse Proxy / Docker) bzgl. TLS.
2. **Docker/EXE/PyPI**
   - Dockerfile kopiert Manifest + SW + Icons nach `/opt/kuasarr/kuasarr/static/`.
   - EXE-Build: sicherstellen, dass PyInstaller statische Assets einschließt.
   - Wheel: `MANIFEST.in` ggf. aktualisieren.
3. **Cache-Busting**
   - Hash-basierte Dateinamen oder Versionskonstante im SW.

### Phase 4 – Qualitätssicherung (1 Tag)
1. **Lighthouse / Web Vitals**
   - Ziel: Performance Score ≥ 90, PWA-Check „installable“.
2. **Browser Tests**
   - Desktop (Chrome/Edge/Firefox) + Android (Chrome, standalone Installation).
   - iOS Safari (manifest + service worker support prüfen, evtl. Workaround).
3. **Regression**
   - Page Load + API Response Benchmark (vor/nach PWA) → sicherstellen, dass SW keinen Overhead erzeugt.
4. **Dokumentation**
   - README Abschnitt „Kuasarr als PWA installieren“.
   - Admin-Hinweise für Cache-Invalidierung bei Updates.

## Performance-Schutz
- Service Worker ausschließlich für statische Assets cache-first; API Requests network-first mit Timeout & Fallback.
- Kein zusätzliche JS-Bundle-Vergrößerung außer SW-Registrierung (<2 KB).
- Monitoring der Load Times via Browser DevTools; optional WebSocket/Long-Polling aus SW ausklammern.

## Abhängigkeiten & Risiken
- HTTPS Pflicht für PWA Features → Deployments ohne TLS können weiterhin laufen, aber ohne Install-Option.
- iOS Einschränkungen (keine Push, begrenzter Storage).
- Benutzer müssen Browsercache aktualisieren; SW-Update-Flow dokumentieren.

## Offene Fragen (geklärt)
1. **Offline-Verhalten**: Es reicht eine statische Fehler-/Hinweisseite, keine API-Daten im Cache.
2. **Push/Background Sync**: Nein – Service Worker bleibt schlank ohne zusätzliche Push-Funktionalität.
3. **Authentifizierung**: Weiterhin wie bisher (Cookie-/Session-basiert), der Service Worker nutzt bestehende Mechanismen.

## Nächste Schritte
~~1. Phase-1 Tasks priorisieren und Tickets erstellen (Manifest + Asset-Inventar).~~
~~2. Proof-of-Concept (Manifest + SW Light) auf Test-Branch, Lighthouse Report einholen.~~
~~3. Rollout-Plan inkl. Dokumentation für Admins vorbereiten.~~

## ✅ Implementierung abgeschlossen

### Erstellte Dateien
- `kuasarr/static/manifest.webmanifest` – PWA Manifest
- `kuasarr/static/sw.js` – Service Worker (Precache + Offline-Fallback)
- `kuasarr/static/offline.html` – Offline-Hinweisseite
- `kuasarr/static/logo-192.png` – 192x192 Icon
- `kuasarr/static/logo-maskable.png` – 512x512 Maskable Icon
- `scripts/generate_pwa_icons.py` – Icon-Generator (einmalig ausgeführt)

### Geänderte Dateien
- `kuasarr/providers/ui/html_templates.py` – PWA Meta-Tags, Manifest-Link, SW-Registrierung
- `setup.py` – Neue statische Dateien in package_data
- `README.md` – PWA-Installationsanleitung hinzugefügt

### Features
- **Installierbar** als Standalone-App (Chrome/Edge/Android/iOS)
- **Offline-Fallback** mit Hinweisseite bei fehlender Verbindung
- **Cache-first** für statische Assets, **Network-first** für API
- **Kein Performance-Overhead** – SW proxyt API-Requests nur bei Offline
- **Automatische Updates** via `skipWaiting()` + `clients.claim()`
