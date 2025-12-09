<!-- hide-decryptor-rollout 2025-11-18 -->

# Einheitliches hide.cx-Handling – Maßnahmenplan

> **Ziel:** Die bereits vorhandene hide.cx-API-Entschlüsselung aus `kuasarr/downloads/linkcrypters/hide.py` soll für alle relevanten Portale genutzt werden, sodass keine Filecrypt-/CapHa-Sonderpfade mehr nötig sind und hide-Container automatisch in direkte Download-Links übersetzt werden.

## 0. Leitplanken & Annahmen

- Die hide.cx-API funktioniert ohne API-Key; einzig der User-Agent aus `shared_state` ist erforderlich.
- Die Funktion `decrypt_links_if_hide()` bleibt zentrale Schnittstelle und wird ggf. erweitert (Timeouts, Retries, Logging).
- CapHa/Captcha-Helper muss nicht erweitert werden; alle Arbeiten passieren im Kuasarr-Core.
- Bestehende Filecrypt- oder andere Linkcrypter-Flows dürfen nicht beeinträchtigt werden.

## 1. Bestandsaufnahme & Gap-Analyse

- [ ] **Bestimme Portale mit hide-Containern**: BY, WD, evtl. DL/AD/weitere – anhand realer Logs/Regex prüfen.
- [ ] **Inventarisiere Linklisten-Flüsse**: Wo entstehen `links = [[url, hoster], ...]`? Welche Reihenfolge (unprotected/protected)?
- [ ] **Dokumentiere aktuelle hide-Nutzung**: Nur WD nutzt `decrypt_links_if_hide()` → Statusnotiz erstellen (README/Plan-Link).

## 2. Gemeinsame Utility-Schicht vorbereiten

- [ ] **Erweitere `decrypt_links_if_hide()`** bei Bedarf:
  - Optionaler Parameter `skip_on_error` / `require_match` zur feineren Kontrolle pro Portal.
  - Bessere Log-Ausgabe (z. B. welcher Portal-Handler aufruft, Anzahl Treffer, HTTP-Fehler).
  - Konfigurierbare Timeouts/Retry-Zahl (ENV/Config `HideCx`-Block).
- [ ] **Unit-Tests** für `unhide_links()` und `decrypt_links_if_hide()` ergänzen (Mock `requests`).

## 3. Portal-spezifische Anpassungen

### 3.1 WD (Referenz)
- [ ] Code reviewen und als Vorlage dokumentieren (Kommentare oder Wiki-Eintrag).

### 3.2 BY
- [ ] Nach dem Einsammeln der Links unmittelbar `decrypt_links_if_hide()` ausführen.
- [ ] Erfolgreiche Dekodierung → `handle_unprotected` mit echten Host-Links.
- [ ] Keine hide-Treffer → regulär (geschützte Links) weitermachen.

### 3.3 Weitere Portale (DL, AD, NX, etc.)
- [ ] Regex/Parser prüfen, ob hide-Container auftauchen können (Logs durchsuchen).
- [ ] Pro Portal entscheiden:
  1. **Direktes Hide-Handling** wie bei BY/WD.
  2. **Delegation erst im Dispatcher** (siehe Abschnitt 4).
- [ ] Änderungen gesammelt testen (siehe Abschnitt 6).

## 4. Dispatcher & Fallback-Logik

- [ ] In `kuasarr/downloads/__init__.py` eine zentrale Hide-Prüfung einbauen, bevor `handle_protected` aufgerufen wird (z. B. Utility `process_hide_links_if_any(shared_state, links, label)`).
- [ ] Rückgabewerte vereinheitlichen (`{"status": "success|none|error", "results": [...]}`) und in allen Handlern korrekt interpretieren.
- [ ] Bei Fehlversuch `StatsHelper`-Zähler erhöhen + informative Fehlermeldung.
- [ ] Sicherstellen, dass Filecrypt-spezifische Pfade nur noch greifen, wenn kein hide-Link erkannt wurde.

## 5. Konfiguration & Dokumentation

- [ ] Neues Config-Cluster `HideCx` (Timeout, Retries, optional Proxy) dokumentieren.
- [ ] README erweitern: Abschnitt „Hide.cx-Unterstützung“ + Troubleshooting.
- [ ] Changelog-Eintrag vorbereiten (Breaking Changes? Nein, aber Hinweis auf neues Verhalten).

## 6. Tests & Qualitätsmaßnahmen

- [ ] **Unit-Tests**: Hide-Utility + betroffene Source-Handler (BY etc.) mit Fixtures.
- [ ] **Integrationstest**: Simulierter WD/BY-Job, der hide-Container liefert → erwartete Direktlinks.
- [ ] **Smoke-Test**: Kompletten Download-Prozess mit einem realen hide-Link durchspielen (Sandbox / Testinstanz).
- [ ] **Regression**: Sicherstellen, dass Filecrypt-Flow weiterhin funktioniert (bestehende Tests ausführen).

## 7. Monitoring & Betrieb

- [ ] Logs auf Portal-Ebene ergänzen (`info`/`debug`: „Hide-Links gefunden“, „Decrypt failed“, Response-Code).
- [ ] Optional: Counter in `StatsHelper` (`hide_links_processed`, `hide_links_failed`).
- [ ] Alert-Doku: Was tun bei API-Änderungen (z. B. 403/5xx)? Fallback-Strategie definieren (erneuter Versuch, Support-Hinweis).

## 8. Rollout-Vorgehen

1. **Feature Branch**: Alle Codeänderungen + Tests.
2. **QA/Staging**: WD/BY-Szenarien mit echten Links validieren.
3. **Release-Notiz**: Hinweis, dass hide-Container jetzt automatisch verarbeitet werden.
4. **Post-Release-Check**: Logs auf Ausreißer prüfen; falls Probleme → temporär Portal-spezifische Hide-Nutzung deaktivieren (Feature-Flag `HIDECX_ENABLED`).

## 9. Offene Fragen & Entscheide

- [ ] Müssen bestimmte Portale zwingend hide nutzen, oder soll Erkennung heuristisch erfolgen (Regex auf URL)?
- [ ] Braucht es eine Retry-Grenze pro Portal (z. B. BY 1 Versuch, WD 3 Versuche)?
- [ ] Soll bei API-Ausfällen automatisch in den Filecrypt-/Captcha-Flow gewechselt werden?

> **Hinweis:** Markiere erledigte Schritte mit `✅` und ergänze bei Bedarf weitere Abschnitte, wenn neue Portale oder Anforderungen hinzukommen.
