# Manuelle Tests für dich

Claude trägt hier Tests ein, die nur mit dem echten Bot in Discord prüfbar sind.
Ergebnisse bitte in `FEEDBACK.md` eintragen.

## T1 – Core-Änderung (Willkommenskanal-Dienst, Fehlerbehandlung)
Einspielen (Core geändert): `cd /home/uik/projects/Worker_Molch && sudo docker compose up -d --build`
1. Warten, bis der Bot online ist.
2. `/ping` ausführen → Erwartet: „Pong! Latenz: … ms“.
3. `/honeypot status` ausführen → Erwartet: Statusanzeige wie bisher, keine Fehlermeldung.
4. `/module list` ausführen → Erwartet: Modulliste wie bisher.
