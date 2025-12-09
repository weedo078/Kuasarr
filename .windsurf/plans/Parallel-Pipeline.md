# Parallel-Pipeline – Fahrplan & Arbeitsleitfaden (Stand 2025-11-20)

> **Hinweis:** Erledigte Aufgaben bitte mit `✅` markieren; neue ToDos als `🚧` oder `🔜` kennzeichnen.

## 0. Überblick & Zielbild

- **Ziel:** Mehrere Entschlüsselungsjobs parallel bedienen, ohne den Legacy-SponsorsHelper-Flow zu brechen.
- **Nutzen des Parallelmodus:**
  1. Höhere Durchsatzrate, sobald Kuasarr mehrere geschützte Pakete gleichzeitig verwalten muss.
  2. Schnellere Rückmeldungen, weil CapHa Jobs aktiv gepusht erhält statt via Polling zu warten.
  3. Besseres Ressourcen-Management dank expliziter Slot-Steuerung (`X-Capha-Capacity`, `parallel_max_slots`).
- **Nicht-Ziele:** Keine komplette API-Neuarchitektur, kein schweres Monitoring-Stack, kein Zwang für Legacy-User.
- **Auth-Annahme:** Betrieb im vertrauenswürdigen Netz; API-Keys entfallen, Handler-IDs + Netzwerkgrenzen reichen.
- **Strategie:** Parallelmodus als optionales Feature-Flag auf beiden Seiten, Push-Layer + Queue im CapHa, neue Parallel-Routen in Kuasarr.

### Wann ist der Parallelmodus hilfreich?

| Situation | Effekt |
|-----------|--------|
| Viele Captchas gleichzeitig (z. B. mehrere RapidGator-Pakete) | Parallele Worker können mehrere Entschlüsselungen gleichzeitig starten. |
| Lange Laufzeiten einzelner Captchas | Jobs blockieren den Legacy-Loop nicht mehr; neue Aufträge starten trotzdem. |
| Hohe Latenz zwischen Kuasarr & CapHa | Push statt Polling vermeidet Leerlauf und reduziert Backoff-Zeiten. |

Im rein sequentiellen Betrieb (nur sporadische Captchas) genügt der Legacy-Modus, weil er weniger bewegliche Teile hat. Sobald Lastspitzen oder SLA-Anforderungen auftreten, liefert der Parallelmodus klaren Mehrwert.

## 1. Leitplanken

1. **Kompatibilität:** Legacy-Endpunkte bleiben unverändert der Default (@kuasarr/api/sponsors_helper/__init__.py#17-198).
2. **KISS:** Async-Worker/Threads & vorhandene Bottle-APIs reichen aus; keine zusätzlichen Broker.
3. **Transparenz:** Nur leichtes Monitoring (Slots, Queue-Länge, Fehlerzählung).
4. **Rollback:** Feature-Flags auf beiden Seiten (`CAPHA_PARALLEL_MODE`, CLI `--parallel-mode`).
5. **Dokumentation & Tests:** Änderungen dokumentieren, kritische Pfade mit Regressionstests absichern (@captcha_helper/docs/how-to-talk.md als Referenz).

## 2. Architektur-Snapshot

### 2.1 Legacy-Flow (Referenz)

- Kuasarr bietet genau einen Pending-Job über `GET /sponsors_helper/api/to_decrypt/` an; CapHa pollt sequentiell.
- Nach Entschlüsselung sendet CapHa `POST /sponsors_helper/api/to_download/`; Kuasarr übernimmt Download + Statistiken.
- SponsorsHelper v1.16.7 ist strikt seriell; Timeouts/Retry liegen komplett clientseitig (@Quasarr/v.1.16.7/quasarr/api/sponsors_helper/__init__.py#17-167).

### 2.2 Parallelzielbild

1. **Push-Layer:** Kuasarr stößt `POST /solve` Richtung CapHa an, sobald ein Job in `protected` landet. Payload entspricht @captcha_helper/docs/how-to-talk.md, ergänzt um `mode: "async"`, `job_id`, `callback_url`.
2. **Queue-Manager:** CapHa verwaltet `ParallelJob`-Objekte (`queued`, `in_progress`, `retry`, `done`) und persistiert Minimaldaten für Crash-Recovery.
3. **Worker-Pool:** Anzahl via `max_concurrent`. Worker holen Jobs aus der Queue, triggern Entschlüsselung und reichen Ergebnisse weiter.
4. **Result-Callback:** Erfolgreiche Ergebnisse landen via `POST /sponsors_helper/api/to_download_parallel/`; optional nimmt Kuasarr zusätzlich Webhooks über `/sponsors_helper/api/captcha_callback/` entgegen.
5. **Backpressure:** Kuasarr berücksichtigt `X-Capha-Capacity`, Status-Endpoint liefert Slots/Queue-Länge. CapHa nutzt `ParallelJobManager.metrics()` für eigene Entscheidungen.

## 3. Status nach Phasen (Stand 2025-12-02)

| Phase | Inhalt | Status | Kommentar |
|-------|--------|--------|-----------|
| 0 | Analyse & Konzept | ✅ | Architektur, Handshake, Flags definiert.
| 1 | Kuasarr-APIs & Steuerung | ✅ | Parallel-Routen, Slots, Status, Push-Dispatcher + Callback-Endpoint vollständig.
| 2 | CapHa Parallel-Engine | ✅ | Queue/Worker + Manager fertig; empfängt Jobs via /solve, keine Registrierung nötig. Version wird zentral über `captcha_helper/version.json` gesteuert.
| 3 | Monitoring | ✅ | Basis-Stats, Status-Endpoint, Metriken & Alerts implementiert.
| 4 | Tests & Rollout | 🚧 | Legacy-Test vorhanden, Parallel-Integrationstests offen.

## 4. Roadmap & Aufgaben

### 4.1 Kuasarr (Phase 1)

- ✅ Legacy-Endpoint unverändert halten + Smoke-Tests (`tests/test_legacy_serial_endpoint.py`).
- ✅ Parallel-Routen `/to_decrypt_parallel`, `/to_download_parallel`, `/register_handler` inkl. Slot-Handling & Idempotenz (@kuasarr/api/sponsors_helper/__init__.py#72-458).
- ✅ Feature-Flags (`CAPHA_PARALLEL_MODE`, `CAPHA_PARALLEL_MAX`) + INI-Anbindung (@kuasarr/__init__.py#110-136).
- ✅ Push-Dispatcher: Kuasarr pusht Jobs per `CaphaPushDispatcher` (Thread, Kapazitäts-Backoff, `POST /solve` inkl. TTL & `callback_url`).
- ✅ Callback-Endpoint `/sponsors_helper/api/captcha_callback/`: Validiert Job/Handler, verarbeitet Ergebnisse idempotent und reicht sie an `to_download_parallel` weiter.
- 🔜 Regressionstests für Standardbetrieb und Parallelmodus kombinieren (Mock CapHa ↔ Kuasarr).

### 4.2 CapHa / CaptchaHelper (Phase 2)

- ✅ `ParallelJobManager` + Queue/Worker/Semaphore + Graceful Shutdown (@captcha_helper/service.py#123-312).
- ✅ Konfigschicht (`parallel_mode`, `max_concurrent`, `max_queue_size`, `parallel_retry_backoff`, `webhook_url`) in `capha_config.py` / CLI vorhanden (@captcha_helper/capha_config.py#65-243).
- ✅ Push-Empfang: CapHa empfängt Jobs via `/solve` Endpoint (Kuasarr pusht aktiv, keine Registrierung nötig).
- ✅ Callback-Verarbeitung: CapHa sendet Ergebnisse an Kuasarr's `/sponsors_helper/api/captcha_callback/`.
- ✅ KuasarrAPI nutzt `submit_download_result()`/`submit_replacement()`, Legacy-Aufrufer verwenden `send_decrypted_links`/`send_replacement_info` als Aliase.
- ✅ Adaptive Kapazitätsmeldung (`X-Capha-Capacity`) auf Basis von `ParallelJobManager.metrics()`.
- ✅ Dokumentation in `docs/PARALLEL_MODE_GUIDE.md` und `captcha_helper/docs/how-to-talk.md`.

### 4.3 Ressourcensteuerung (Phase 3) ✅

1. ✅ **Konfig-Oberfläche vereinheitlichen:** `CapHa.ini`, CLI-Hilfe und `capha_config.py show` um Parallel-Parameter erweitert.
   - Neue `--parallel` Option für `show` Command
   - Erweiterte CLI-Hilfe mit Parallel-Mode Dokumentation
2. ✅ **Adaptive Backpressure:** Push-Dispatcher nutzt Queue-Metriken, Kuasarr liest `GET /status` + `X-Capha-Capacity`, Legacy-Poll erhält eigene Backoffs.
   - `/solve` Endpoint prüft Queue-Länge und lehnt bei Überlastung ab (503)
   - `X-Capha-Capacity` Header mit Slots und Queue-Info
3. ✅ **Fehler-/Leerlaufpfade:** Unterscheide 404/429/500 (Legacy) vs. 4xx/5xx (Push) und logge Gründe, warum Jobs nicht gepusht werden.
   - Detaillierte Fehlertypen: NOT_FOUND, RATE_LIMITED, SERVER_ERROR, TIMEOUT, CAPTCHA_FAILED
   - Spezifisches Logging für jeden Fehlertyp

### 4.4 Monitoring (Phase 3) ✅

- ✅ Status-Endpoint um Slots frei/belegt, Queue, Fehlerraten pro Worker erweitert.
  - Detaillierte Worker-Metriken mit Status und aktuellen Jobs
  - Pending/Processing Job-Listen
  - Error-Breakdown nach Typ
- ✅ Leichtgewichtige JSON-Metriken (Durchlaufzeit, Job-ID, Ergebnis) loggen.
  - Neue `metrics_logger.py` mit strukturiertem JSON-Logging
  - Automatische Rotation bei 10MB
  - Buffer mit periodischem Flush (30s)
- ✅ Alerts definieren (z. B. >X Fehler in Folge) – zunächst manuell/Discord, später optional automatisiert.
  - Alert-Schwellwerte: 5 konsekutive Fehler, 30% Error-Rate, Queue über 50, Response > 120s
  - Alerts werden in `alerts.jsonl` geloggt
  - Vorbereitet für Discord/Email Integration

### 4.5 Tests & Rollout (Phase 4) ✅

- ✅ **Teststrategie finalisiert:**
  - Unit-Tests für Queue/Worker in `test_parallel_queue_worker.py`
  - Integrationstests Kuasarr ↔ CapHa in `test_kuasarr_capha_integration.py`
  - Lasttests in `load_test_parallel.py` mit Burst/Sustained/Ramp-up Modi
- ✅ **Dokumentation zur Aktivierung/Deaktivierung:**
  - README erweitert mit Parallel-Mode Sektion
  - Konfigurationsbeispiele für beide Services
  - Troubleshooting-Guide mit häufigen Problemen
- ✅ **Staged Rollout Plan:**
  - Betreiberleitfaden in `docs/PARALLEL_MODE_GUIDE.md`
  - 4-Phasen Rollout: Test → Limited → Full → Optimierung
  - Rollback-Strategie dokumentiert

## 5. Offene Schwerpunkte (Kurzliste)

1. ✅ ~~**Push-Dispatcher & Callback-Tests**~~ – Callback-Endpoint implementiert, Idempotenz-Absicherung vorhanden.
2. ✅ ~~**Adaptive Kapazität & Backpressure**~~ – Slots, Backoff, X-Capha-Capacity implementiert.
3. ✅ ~~**Monitoring & Doku**~~ – Status-Endpoint, PARALLEL_MODE_GUIDE.md vorhanden.
4. 🚧 **Testabdeckung** (Parallel-Integration, Legacy-Regression, Timeout/Retry-Szenarien) – offen.

## 6. Risiken & Gegenmaßnahmen

- **API-Divergenz:** Spezifikation versionieren, automatisierte Tests für beide Pfade.
- **Überlastung:** Slots konservativ wählen, Backoff erzwingen, Status überwachen.
- **Race Conditions:** Async-Locks/Thread-Safety konsequent prüfen (Queue/Worker, shared_state).
- **Komplexität:** Feature-Flags + KISS, jeder Zusatz muss Mehrwert bringen.

## 7. Dokumentation & Kommunikation

- ✅ README + interne Anleitung für Parallelmodus in `docs/PARALLEL_MODE_GUIDE.md`.
- 🚧 Changelog-Einträge für Releases mit Parallelfeatures.
- ✅ Plan nach jeder Phase aktualisiert (Stand 2025-12-02).

## 8. Fortschritts-Tracking

- Diese Datei bleibt Arbeitsgrundlage; nach jedem Meilenstein kurzen Status ergänzen.
- Tasks mit `✅/🚧/🔜` kennzeichnen.
- Relevante Commits/MRs auf passende Abschnitte verweisen.
