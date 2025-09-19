#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Schnelle Überprüfung welche Browser-Prozesse laufen
"""

import subprocess

def check_browsers():
    """Prüft laufende Browser-Prozesse"""
    try:
        result = subprocess.run([
            'powershell.exe', '-c', 
            'Get-Process | Where-Object {$_.ProcessName -match "chrome|msedge|firefox"} | Select-Object ProcessName, Id, CPU'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            output = result.stdout.strip()
            if output and len(output.split('\n')) > 2:
                print("🔍 Laufende Browser-Prozesse:")
                print(output)
                
                # Zähle Prozesse
                lines = output.split('\n')[2:]  # Skip headers
                processes = {}
                for line in lines:
                    if line.strip():
                        parts = line.strip().split()
                        if len(parts) >= 1:
                            proc_name = parts[0].lower()
                            if proc_name in ['chrome', 'msedge', 'firefox']:
                                processes[proc_name] = processes.get(proc_name, 0) + 1
                
                print(f"\n📊 Zusammenfassung:")
                browser_names = {
                    'chrome': 'Google Chrome',
                    'msedge': 'Microsoft Edge',
                    'firefox': 'Mozilla Firefox'
                }
                
                for proc, count in processes.items():
                    print(f"  - {browser_names.get(proc, proc)}: {count} Prozesse")
                
                if processes:
                    print(f"\n💡 Für Cookie-Extraktion sollten alle Browser geschlossen werden.")
                    print(f"   Beende sie mit Task Manager oder schließe alle Browser-Fenster.")
                
            else:
                print("✅ Keine Browser-Prozesse gefunden - bereit für Cookie-Extraktion!")
        
    except Exception as e:
        print(f"❌ Fehler beim Prüfen der Prozesse: {e}")

if __name__ == "__main__":
    print("🚀 Browser-Prozess-Checker")
    print("=" * 40)
    check_browsers() 