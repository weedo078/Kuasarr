# 🍪 data-load.me Cookie-Integration für Quasarr

## Überblick

Das neue Cookie-System ermöglicht es, bereits vorhandene Browser-Sessions für data-load.me in Quasarr zu verwenden. Dies umgeht **alle Login-Probleme** (CAPTCHA, 2FA, komplexe Formulare, etc.) und ist viel benutzerfreundlicher als die manuelle Credentials-Eingabe.

## Vorteile

✅ **Keine Login-Probleme mehr** - nutzt funktionierende Browser-Sessions  
✅ **Umgeht CAPTCHA und 2FA** - Browser hat bereits alle Authentifizierungen  
✅ **Automatische Extraktion** - unterstützt Chrome, Firefox und Edge  
✅ **Fallback-System** - Credentials bleiben als Backup verfügbar  
✅ **Cross-Platform** - funktioniert unter Windows, macOS und Linux  

## Schnellstart

### 1. Cookie-Extraktor verwenden

```bash
# 1. Alle Browser schließen
# 2. Cookie-Extraktor ausführen
python extract_dl_cookies.py

# 3. dl_cookies.json wird erstellt
```

### 2. Cookies in Quasarr verwenden

**Option A: Docker-Umgebungsvariable**
```bash
docker run -d \
  --name quasarr-dl \
  -p 8080:8080 \
  -e DL_COOKIES=/config/dl_cookies.json \
  -v /pfad/zu/config:/config \
  -v /pfad/zu/dl_cookies.json:/config/dl_cookies.json \
  quasarr-dl:latest
```

**Option B: Config-Verzeichnis**
```bash
# Einfach dl_cookies.json ins Quasarr config-Verzeichnis kopieren
cp dl_cookies.json /path/to/quasarr/config/
```

## Detaillierte Anleitung

### Schritt 1: Browser-Login

1. **Öffne deinen Browser** (Chrome, Firefox oder Edge)
2. **Gehe zu data-load.me** und logge dich normal ein
3. **Stelle sicher, dass du eingeloggt bist** (siehst du dein Profil?)
4. **Schließe den Browser komplett**

### Schritt 2: Cookie-Extraktion

```bash
# Cookie-Extraktor ausführen
python extract_dl_cookies.py
```

**Beispiel-Output:**
```
🍪 Cookie-Extraktor für data-load.me
==================================================
[Chrome] Lese Cookies aus: C:\Users\...\Google\Chrome\...\Cookies
[Chrome] ✅ 8 Cookies für data-load.me gefunden
✅ Cookies gespeichert in: dl_cookies.json
📊 Insgesamt 8 Cookies extrahiert

🔍 Gefundene Cookies:
  - xf_session
  - xf_user
  - xf_csrf
  - xf_lang
  - ...
```

### Schritt 3: Cookie-Datei Format

Die `dl_cookies.json` hat folgendes Format:

```json
{
  "cookies": {
    "xf_session": "abcd1234...",
    "xf_user": "12345,hash...",
    "xf_csrf": "csrf_token..."
  },
  "metadata": {
    "domain": "data-load.me",
    "extracted_at": "2025-01-11T17:30:00",
    "total_cookies": 8,
    "cookie_details": { ... }
  }
}
```

### Schritt 4: Quasarr-Integration

**Docker-Deployment:**

```bash
# Vollständiger Docker-Befehl mit Cookie-Support
docker run -d \
  --name quasarr-dl \
  -p 8080:8080 \
  -e INTERNAL_ADDRESS=http://192.168.1.100:8080 \
  -e EXTERNAL_ADDRESS=http://192.168.1.100:8080 \
  -e HOSTNAMES=dl:www.data-load.me \
  -e DL_COOKIES=/config/dl_cookies.json \
  -e DL_USER=fallback_user \
  -e DL_PASSWORD=fallback_password \
  -v /host/config:/config \
  -v /host/dl_cookies.json:/config/dl_cookies.json \
  quasarr-dl:latest
```

**Lokale Installation:**

```bash
# Cookie-Datei ins Config-Verzeichnis
cp dl_cookies.json ~/.config/quasarr/

# Umgebungsvariable setzen
export DL_COOKIES=~/.config/quasarr/dl_cookies.json

# Quasarr starten
python -m quasarr
```

## Cookie-Pfad-Priorität

Quasarr sucht Cookies in folgender Reihenfolge:

1. **`DL_COOKIES` Umgebungsvariable**
2. **Quasarr Config** (`shared_state.config.DL.cookies`)
3. **`/config/dl_cookies.json`** (Standard Docker-Pfad)
4. **`dl_cookies.json`** (Aktuelles Verzeichnis)

## Automatische Session-Speicherung

Wenn Quasarr erfolgreich mit Credentials einloggt, werden die Session-Cookies **automatisch gespeichert** für zukünftige Verwendung:

```
[DL-INIT] ✅ Session erfolgreich erstellt für benutzer
[DL-COOKIES] Session-Cookies gespeichert: /config/dl_cookies.json
```

## Fehlerbehebung

### Problem: Keine Cookies gefunden

```
[DL-COOKIES] Keine Cookie-Datei gefunden
```

**Lösung:**
- Stelle sicher, dass `dl_cookies.json` im richtigen Pfad liegt
- Prüfe die `DL_COOKIES` Umgebungsvariable
- Führe `extract_dl_cookies.py` erneut aus

### Problem: Cookie-Session ungültig

```
[DL-COOKIES] ❌ Cookie-Session ungültig - Cookies möglicherweise abgelaufen
```

**Lösung:**
- Logge dich erneut im Browser bei data-load.me ein
- Führe `extract_dl_cookies.py` erneut aus
- Cookies haben meist eine Lebensdauer von 30-90 Tagen

### Problem: Browser-Cookies nicht gefunden

```
[Chrome] ❌ Keine Chrome-Cookie-Datei gefunden
```

**Lösung:**
- Stelle sicher, dass der Browser komplett geschlossen ist
- Prüfe ob Chrome/Firefox/Edge installiert ist
- Führe das Script mit Admin-Rechten aus (Windows)

## Logs überwachen

```bash
# Docker-Logs überwachen
docker logs -f quasarr-dl

# Nach Cookie-relevanten Meldungen filtern
docker logs quasarr-dl | grep -E "(DL-COOKIES|Cookie)"
```

**Erfolgreiche Cookie-Integration:**
```
[DL-COOKIES] Lade Cookies aus: /config/dl_cookies.json
[DL-COOKIES] 8 Cookies geladen
[DL-COOKIES] ✅ Cookie-Session erfolgreich validiert
[DL-COOKIES] Cookie-Metadaten: 2025-01-11T17:30:00
```

## Sicherheitshinweise

⚠️ **Cookie-Datei enthält sensible Daten** - sichere Aufbewahrung!  
⚠️ **Keine Cookies in öffentliche Repositories** committen  
⚠️ **Regelmäßige Cookie-Erneuerung** (alle 30-60 Tage empfohlen)  

## Erweiterte Funktionen

### Manuelle Cookie-Bearbeitung

Du kannst `dl_cookies.json` manuell bearbeiten:

```json
{
  "cookies": {
    "xf_session": "DEINE_SESSION_ID",
    "xf_user": "DEINE_USER_ID"
  }
}
```

### Mehrere Browser-Profile

Wenn du mehrere Browser-Profile hast:

```bash
# Spezifisches Chrome-Profil
export CHROME_PROFILE="Profile 1"
python extract_dl_cookies.py
```

### Cookie-Export aus Browser-Entwicklertools

Alternative: Manuelle Cookie-Extraktion über Browser-Entwicklertools:

1. **F12** drücken → **Application/Storage** Tab
2. **Cookies** → **data-load.me** auswählen  
3. **Wichtige Cookies kopieren:** `xf_session`, `xf_user`, `xf_csrf`
4. **JSON manuell erstellen**

## Support

Bei Problemen mit dem Cookie-System:

1. **Überprüfe die Logs** auf Cookie-bezogene Fehlermeldungen
2. **Teste Browser-Login** - funktioniert data-load.me im Browser?
3. **Führe Cookie-Extraktor erneut aus** mit geschlossenen Browsern
4. **Fallback auf Credentials** - setze `DL_USER` und `DL_PASSWORD` als Backup

Das Cookie-System ist als **Primary-Lösung** gedacht, mit Credentials als **Fallback** für maximale Zuverlässigkeit! 