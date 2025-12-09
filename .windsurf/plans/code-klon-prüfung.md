**Plan zur Code-Klon-Prüfung**

1. **Referenzbasis festlegen**
   - Originalverzeichnis sichern (hier: `captcha_helper/neue_version_2025-11-09_11-55-50`).
   - Zielverzeichnis definieren (aktueller CapHa-Code).  
   - Notieren, welche Teile bewusst neu implementiert oder übernommen wurden (z. B. Datenstrukturen, Assets).

2. **Automatischer Vergleich (Struktur & Text)**
   1. Dateiliste und Größen vergleichen (`tree`, `du`, `find`). Auffällige 1:1-Dateinamen notieren.
   2. Hash-basierte Diff-Checks (z. B. `shasum`/`md5sum` auf Dateien gleicher Größe).
   3. Zeilenbasierte Diffs für Kandidaten (`diff -ru`, `git diff --no-index`). Nur identische oder nahezu identische Abschnitte flaggen.
   4. Optional: Plagiats-Scanner (z. B. `simian`, `jplag`) für zusätzliche Sicherheit.

3. **Semantische Prüfung**
   - Prüfen, ob besondere Algorithmen/Protokolle lediglich in derselben Logik umgesetzt wurden oder wortwörtlich übernommen sind.
   - Kommentare, Strings, Logmeldungen vergleichen – identische Formulierungen deuten auf Kopien hin.
   - Assets prüfen (Bilder, Configs, Skripte). Identische Checksummen → potenziell kopiert.

4. **Clean-Room-Nachweis**
   - Dokumentation/Notizen der Neuentwicklung zusammentragen (eigene Spezifikationen, Chat-Logs mit Agents).
   - Prüfen, ob neue Dateien ausreichend eigene Struktur aufweisen (Namensgebung, Modulaufteilung).
   - Ergebnisse in einem Prüfprotokoll festhalten: Datum, Tool-Ausgabe, Bewertung.

5. **Entscheidung & Empfehlungen**
   - Wenn identische Passagen gefunden: beurteilen, ob sie trivial (z. B. Standard-Boilerplate) oder schutzwürdig sind.
   - Bei Unklarheiten: Referenz zum Autor herstellen oder rechtliche Einschätzung einholen.
   - Clean-Room-Bericht + Tool-Outputs archivieren, um bei Veröffentlichung nachweisen zu können, dass kein 1:1-Kopieren vorliegt.