# Manuelle Tests für dich

Claude trägt hier Tests ein, die nur mit dem echten Bot in Discord prüfbar sind.
Ergebnisse bitte in `FEEDBACK.md` eintragen.

## T1 – Core-Intents (Aufgabe 1)
Einspielen: `cd /home/uik/projects/Worker_Molch && sudo docker compose up -d --build`
**Vorher** im Discord Developer Portal → Bot → „Message Content Intent“ aktivieren (sonst startet der Bot nicht: `PrivilegedIntentsRequired`).
1. Bot nach dem Rebuild starten, `docker compose logs -f` ansehen.
2. In Discord `/ping` ausführen.
- Erwartet: Bot meldet „Bot angemeldet als …“ ohne Fehler; `/ping` antwortet mit „Pong! Latenz: … ms“; `/module` und `/clear` funktionieren weiter.
