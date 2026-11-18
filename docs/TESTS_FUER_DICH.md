# Manuelle Tests für dich

Claude trägt hier Tests ein, die nur mit dem echten Bot in Discord prüfbar sind.
Ergebnisse bitte in `FEEDBACK.md` eintragen.

## T1 – Core-Intents (Aufgabe 1)
Einspielen: `cd /home/uik/projects/Worker_Molch && sudo docker compose up -d --build`
**Vorher** im Discord Developer Portal → Bot → „Message Content Intent“ aktivieren (sonst startet der Bot nicht: `PrivilegedIntentsRequired`).
1. Bot nach dem Rebuild starten, `docker compose logs -f` ansehen.
2. In Discord `/ping` ausführen.
- Erwartet: Bot meldet „Bot angemeldet als …“ ohne Fehler; `/ping` antwortet mit „Pong! Latenz: … ms“; `/module` und `/clear` funktionieren weiter.

## T2 – Modul laden und `/honeypot status` (Aufgabe 4)
Einspielen: Rebuild aus T1 muss durch sein. Dann in Discord `/module enable honeypot` (bei späteren Änderungen: `/module reload honeypot`).
1. Tippe `/honeypot` – es sollten 7 Unterbefehle erscheinen: start, stop, status, channel, setrole, removerole, setlanguage.
2. Führe `/honeypot status` aus.
3. Optional: mit einem Account ohne „Mitglieder bannen“ `/honeypot status` versuchen.
- Erwartet: Nur für dich sichtbare Antwort: Überwachung inaktiv, Channel nicht gesetzt, Save-Roles keine, Sprache DEUTSCH, Gebannte User 0.
  Account ohne Recht: Befehl nicht sichtbar bzw. Meldung „Mitglieder bannen“ fehlt. Die anderen Befehle antworten vorerst „noch nicht verfügbar“.
