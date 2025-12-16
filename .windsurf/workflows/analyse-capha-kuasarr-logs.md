---
description: Analysiert CapHa und Kuasarr Docker-Logs auf Unraid-Host und schlägt Lösungen vor
---
1. Stelle sicher, dass der SSH-Schlüssel unter `C:\Users\gianj\.ssh\Unraid` verfügbar ist.
2. Verbinde dich via `ssh -i "C:\Users\gianj\.ssh\Unraid" root@192.168.178.5` mit dem Host.
3. Führe `docker logs --tail 500 CapHa` aus und notiere Fehler, Warnungen oder ungewöhnliche Ausgaben.
4. Führe `docker logs --tail 500 Kuasarr` aus und protokolliere relevante Meldungen.
5. Analysiere beide Logausgaben auf Ursachen (z. B. Netzwerkprobleme, Exceptions, Ressourcenmangel).
6. Erstelle eine kurze Problembeschreibung und schlage konkrete Lösungs- oder Mitigationsschritte vor.
