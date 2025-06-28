# Integration von data-load.me in Quasarr

## Aufgabenliste

1. **Erstellung neuer Quelldateien:**
   - Neue Suchdatei `dl.py` im Verzeichnis `quasarr/search/sources/` erstellen
   - Neue Download-Datei `dl.py` im Verzeichnis `quasarr/downloads/sources/` erstellen

2. **Implementierung der Suchfunktionen in der Suchdatei:**
   - `dl_search` Funktion für die gezielte Suche nach Inhalten
   - `dl_feed` Funktion für das Abrufen aktueller Releases
   - Hilfsfunktionen für Dateigrößenextraktion, Veröffentlichungsdatum usw.

3. **Implementierung der Download-Funktionen in der Download-Datei:**
   - Authentifizierungsfunktionen (falls data-load.me ein Login benötigt)
   - Funktionen zum Extrahieren der tatsächlichen Download-Links
   - Funktionen zur Verarbeitung von CAPTCHA oder anderen Schutzmechanismen

4. **Aktualisierung der Hauptsuchdatei:**
   - Import der neuen Funktionen in `quasarr/search/__init__.py`
   - Hinzufügen der neuen Quelle zu den bestehenden Suchfunktionen

5. **Aktualisierung der Konfiguration:**
   - Hinzufügen eines neuen Eintrags für data-load.me in der Konfigurationsstruktur
   - Aktualisierung der zulässigen Hostnamen in der Konfigurationsdatei

6. **Anpassung der Benutzeroberfläche:**
   - Falls notwendig, Anpassung der Weboberfläche für data-load.me-spezifische Funktionen

7. **Testen:**
   - Testen der Suchfunktionen mit verschiedenen Suchbegriffen
   - Testen der Download-Funktionen mit verschiedenen Inhalten
   - Prüfen der Integration mit Sonarr/Radarr

8. **Dokumentation:**
   - Aktualisierung der README.md mit Informationen zur neuen Quelle
   - Hinzufügen von Konfigurationshinweisen für data-load.me

## Technische Anforderungen

1. **Analyse der data-load.me-Webseite:**
   - Untersuchung der API oder Webschnittstelle
   - Identifizierung von Authentifizierungsmechanismen
   - Analyse der Suchparameter und -ergebnisse
   - Verständnis des Download-Prozesses

2. **Implementierungsdetails:**
   - Verwendung von BeautifulSoup für das Parsen von HTML (falls keine API vorhanden)
   - Implementierung von Authentifizierungsmechanismen (falls erforderlich)
   - Verarbeitung von CAPTCHA oder anderen Schutzmechanismen (falls vorhanden)
   - Integration mit dem bestehenden Quasarr-System zum Weiterleiten der Links an JDownloader

3. **Konfigurationsanforderungen:**
   - Speicherung von Zugangsdaten für data-load.me (falls erforderlich)
   - Konfiguration von Suchparametern und -filtern

## Code-Struktur

Basierend auf der Analyse des bestehenden Codes sollte die neue Quellimplementierung folgendem Muster folgen:

### Suchdatei (quasarr/search/sources/dl.py)

```python
# -*- coding: utf-8 -*-
# Quasarr
# Project by https://github.com/rix1337

import html
import re
import time
from base64 import urlsafe_b64encode
from datetime import datetime

# Weitere Importe

from quasarr.providers.imdb_metadata import get_localized_title
from quasarr.providers.log import info, debug

def dl_feed(shared_state, start_time, request_from):
    releases = []
    dl = shared_state.values["config"]("Hostnames").get("dl")
    password = dl
    
    # Implementierung der Feed-Funktion
    
    return releases

def dl_search(shared_state, start_time, request_from, search_string):
    releases = []
    dl = shared_state.values["config"]("Hostnames").get("dl")
    password = dl
    
    # Implementierung der Suchfunktion
    
    return releases
```

### Download-Datei (quasarr/downloads/sources/dl.py)

```python
# -*- coding: utf-8 -*-
# Quasarr
# Project by https://github.com/rix1337

import re
import time
from urllib.parse import quote_plus, unquote_plus

# Weitere Importe

from quasarr.providers.log import info, debug

def create_and_persist_session(shared_state):
    # Implementierung für Session-Erstellung
    pass

def retrieve_and_validate_session(shared_state):
    # Implementierung für Session-Validierung
    pass
    
def get_dl_download_link(shared_state, url):
    # Implementierung für Download-Link-Extraktion
    pass
```

### Aktualisierung der Hauptsuchdatei (quasarr/search/__init__.py)

```python
# Hinzufügen des Imports
from quasarr.search.sources.dl import dl_feed, dl_search

# Aktualisierung der get_search_results Funktion
def get_search_results(shared_state, request_from, search_string="", season="", episode=""):
    # ...
    
    dl = shared_state.values["config"]("Hostnames").get("dl")
    
    # ...
    
    if search_string:
        # ...
        if dl:
            functions.append(lambda: dl_search(shared_state, start_time, request_from, search_string))
    else:
        # ...
        if dl:
            functions.append(lambda: dl_feed(shared_state, start_time, request_from))
``` 