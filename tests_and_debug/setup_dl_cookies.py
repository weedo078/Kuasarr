#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Automatischer Cookie-Setup für Quasarr data-load.me Integration
- Extrahiert Cookies aus Browser
- Kopiert sie ins Docker-Volume
- Startet Container neu falls nötig
"""

import os
import json
import subprocess
import sys
from pathlib import Path

def run_command(cmd, capture_output=True):
    """Führt einen Shell-Befehl aus"""
    try:
        if capture_output:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
        else:
            result = subprocess.run(cmd, shell=True)
            return result.returncode == 0, "", ""
    except Exception as e:
        return False, "", str(e)

def check_docker():
    """Prüft ob Docker verfügbar ist"""
    print("🐳 Prüfe Docker-Verfügbarkeit...")
    success, stdout, stderr = run_command("docker --version")
    if success:
        print(f"✅ Docker gefunden: {stdout}")
        return True
    else:
        print(f"❌ Docker nicht verfügbar: {stderr}")
        return False

def check_container_exists(container_name="quasarr-dl"):
    """Prüft ob Container existiert"""
    print(f"🔍 Prüfe Container '{container_name}'...")
    success, stdout, stderr = run_command(f"docker ps -a --filter name={container_name} --format '{{{{.Names}}}}'")
    
    if success and container_name in stdout:
        print(f"✅ Container '{container_name}' gefunden")
        return True
    else:
        print(f"⚠️ Container '{container_name}' nicht gefunden")
        return False

def extract_cookies():
    """Extrahiert Cookies mit dem Cookie-Extraktor"""
    print("\n🍪 Starte Cookie-Extraktion...")
    
    # Prüfe auf automatisierte Version zuerst
    if os.path.exists("extract_dl_cookies_auto.py"):
        print("📄 Führe automatisierten Cookie-Extraktor aus...")
        success, stdout, stderr = run_command("python extract_dl_cookies_auto.py --auto", capture_output=True)
        
        if success and os.path.exists("dl_cookies.json"):
            print("✅ Cookie-Datei erfolgreich erstellt: dl_cookies.json")
            return True
        else:
            print(f"❌ Automatisierte Cookie-Extraktion fehlgeschlagen: {stderr}")
    
    # Fallback auf normale Version
    elif os.path.exists("extract_dl_cookies.py"):
        print("📄 Führe Cookie-Extraktor aus (interaktiv)...")
        print("⚠️ Browser bitte schließen und Enter drücken wenn bereit...")
        success, stdout, stderr = run_command("python extract_dl_cookies.py", capture_output=False)
        
        if os.path.exists("dl_cookies.json"):
            print("✅ Cookie-Datei erfolgreich erstellt: dl_cookies.json")
            return True
        else:
            print("❌ Cookie-Extraktion fehlgeschlagen")
            print(f"Fehler: {stderr}")
            return False
    else:
        print("❌ Cookie-Extraktor nicht gefunden!")
        print("Benötigte Dateien: extract_dl_cookies_auto.py oder extract_dl_cookies.py")
        return False

def copy_cookies_to_container(container_name="quasarr-dl", cookie_file="dl_cookies.json"):
    """Kopiert Cookie-Datei ins Docker-Volume"""
    print(f"\n📦 Kopiere Cookies in Container '{container_name}'...")
    
    if not os.path.exists(cookie_file):
        print(f"❌ Cookie-Datei '{cookie_file}' nicht gefunden!")
        return False
    
    # Kopiere Cookie-Datei in Container
    cmd = f"docker cp {cookie_file} {container_name}:/config/dl_cookies.json"
    success, stdout, stderr = run_command(cmd)
    
    if success:
        print("✅ Cookie-Datei erfolgreich in Container kopiert")
        
        # Prüfe ob Datei im Container angekommen ist
        success, stdout, stderr = run_command(f"docker exec {container_name} ls -la /config/dl_cookies.json")
        if success:
            print(f"📋 Container-Dateinfo: {stdout}")
            return True
        else:
            print("⚠️ Cookie-Datei nicht im Container sichtbar")
            return False
    else:
        print(f"❌ Fehler beim Kopieren: {stderr}")
        return False

def restart_container(container_name="quasarr-dl"):
    """Startet Container neu"""
    print(f"\n🔄 Starte Container '{container_name}' neu...")
    
    # Container stoppen
    success, stdout, stderr = run_command(f"docker stop {container_name}")
    if not success:
        print(f"⚠️ Fehler beim Stoppen: {stderr}")
    
    # Container starten
    success, stdout, stderr = run_command(f"docker start {container_name}")
    if success:
        print("✅ Container erfolgreich neu gestartet")
        return True
    else:
        print(f"❌ Fehler beim Starten: {stderr}")
        return False

def validate_cookies_in_container(container_name="quasarr-dl"):
    """Prüft ob Cookies im Container geladen werden"""
    print(f"\n🔍 Validiere Cookie-Integration...")
    
    # Warte kurz für Container-Start
    import time
    time.sleep(3)
    
    # Prüfe Container-Logs auf Cookie-Meldungen
    success, stdout, stderr = run_command(f"docker logs {container_name}")
    if success:
        if "[DL-COOKIES]" in stdout:
            print("✅ Cookie-Integration in Logs gefunden")
            
            # Zeige relevante Log-Einträge
            lines = stdout.split('\n')
            cookie_lines = [line for line in lines if "[DL-COOKIES]" in line]
            
            print("\n📋 Cookie-relevante Log-Einträge:")
            for line in cookie_lines[-5:]:  # Letzte 5 Einträge
                print(f"  {line}")
            
            return True
        else:
            print("⚠️ Keine Cookie-Integration in Logs gefunden")
            print("Container-Logs (letzte 10 Zeilen):")
            lines = stdout.split('\n')
            for line in lines[-10:]:
                print(f"  {line}")
            return False
    else:
        print(f"❌ Fehler beim Lesen der Container-Logs: {stderr}")
        return False

def show_manual_alternatives():
    """Zeigt manuelle Alternativen"""
    print("\n🛠️ Manuelle Alternativen:")
    print("1. Cookie-Datei manuell kopieren:")
    print("   docker cp dl_cookies.json quasarr-dl:/config/dl_cookies.json")
    
    print("\n2. Cookie-Datei ins Host-Verzeichnis legen:")
    print("   # Verwende ein Host-Volume statt Docker-Volume")
    print("   docker run -v /host/path:/config ...")
    
    print("\n3. Container mit Cookie-Volume neu erstellen:")
    print("   docker stop quasarr-dl && docker rm quasarr-dl")
    print("   docker run -d --name quasarr-dl -p 8080:8080 \\")
    print("     -e DL_COOKIES=/config/dl_cookies.json \\")
    print("     -v quasarr_config_dl:/config \\")
    print("     -v $(pwd)/dl_cookies.json:/config/dl_cookies.json \\")
    print("     quasarr-dl:latest")

def main():
    """Hauptfunktion"""
    print("🚀 Automatischer data-load.me Cookie-Setup für Quasarr")
    print("=" * 60)
    
    # Schritt 1: Docker prüfen
    if not check_docker():
        return False
    
    # Schritt 2: Container prüfen
    container_exists = check_container_exists()
    
    # Schritt 3: Cookie-Extraktion
    print("\n" + "="*30 + " COOKIE-EXTRAKTION " + "="*30)
    
    if os.path.exists("dl_cookies.json"):
        print("📄 dl_cookies.json bereits vorhanden")
        use_existing = input("Vorhandene Cookie-Datei verwenden? (j/n): ").lower().startswith('j')
        
        if not use_existing:
            print("🔄 Extrahiere neue Cookies...")
            if not extract_cookies():
                print("❌ Cookie-Extraktion fehlgeschlagen!")
                return False
    else:
        print("🆕 Keine Cookie-Datei gefunden - starte Extraktion...")
        if not extract_cookies():
            print("❌ Cookie-Extraktion fehlgeschlagen!")
            return False
    
    # Schritt 4: Cookies in Container kopieren
    print("\n" + "="*30 + " CONTAINER-DEPLOYMENT " + "="*30)
    
    if not container_exists:
        print("⚠️ Container nicht gefunden!")
        print("Bitte erst Container erstellen:")
        print("docker run -d --name quasarr-dl -p 8080:8080 -v quasarr_config_dl:/config quasarr-dl:latest")
        return False
    
    if not copy_cookies_to_container():
        print("❌ Cookie-Deployment fehlgeschlagen!")
        show_manual_alternatives()
        return False
    
    # Schritt 5: Container neu starten
    print("\n" + "="*30 + " CONTAINER-NEUSTART " + "="*30)
    if not restart_container():
        print("❌ Container-Neustart fehlgeschlagen!")
        return False
    
    # Schritt 6: Validierung
    print("\n" + "="*30 + " VALIDIERUNG " + "="*30)
    if validate_cookies_in_container():
        print("\n🎉 Cookie-Setup erfolgreich abgeschlossen!")
        print("\n✅ Nächste Schritte:")
        print("1. Gehe zu http://192.168.178.207:8080")
        print("2. Teste 'Better Call Saul S01' Download")
        print("3. Prüfe ob Links in JDownloader ankommen")
        return True
    else:
        print("\n⚠️ Cookie-Setup abgeschlossen, aber Validierung unvollständig")
        print("Prüfe die Container-Logs manuell:")
        print("docker logs -f quasarr-dl")
        return True

if __name__ == "__main__":
    try:
        success = main()
        if success:
            print("\n🎯 Setup abgeschlossen!")
        else:
            print("\n❌ Setup fehlgeschlagen!")
            show_manual_alternatives()
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⏹️ Setup abgebrochen")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unerwarteter Fehler: {e}")
        sys.exit(1) 