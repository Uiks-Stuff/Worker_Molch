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

## T3 – `/honeypot setrole` und `removerole` (Aufgabe 5)
Einspielen: `/module reload honeypot`
1. `/honeypot setrole rolle1:<Rolle A> rolle2:<Rolle B>` → Antwort „Hinzugefügt: …“.
2. `/honeypot setrole rolle1:<Rolle A>` erneut → „Bereits Save-Role“.
3. `/honeypot setrole rolle1:@everyone` → „Nicht erlaubt“. Ebenso mit einer Bot-/Integrationsrolle.
4. `/honeypot status` → Save-Roles zeigt A und B.
5. `/honeypot removerole rolle1:<Rolle A> rolle2:<Rolle C ohne Save-Role>` → „Entfernt: A“, „Keine Save-Role: C“.
6. `/honeypot status` → nur noch B. Nach `/module reload honeypot` bleibt B erhalten.
- Erwartet: wie beschrieben, alle Antworten nur für dich sichtbar.

## T4 – `/honeypot channel` (Aufgabe 7)
Einspielen: `/module reload honeypot`
1. `/honeypot channel channel:#test1` → „Honeypot-Channel gesetzt“, Hinweis „Überwachung ist inaktiv“; in #test1 erscheint noch KEINE Nachricht.
2. `/honeypot channel channel:#test1` erneut → „bereits der Honeypot-Channel“.
3. `/honeypot status` → Channel #test1.
4. `/honeypot channel` ohne Angabe → „Honeypot-Channel entfernt“; status zeigt „nicht gesetzt“.
(Wechsel bei aktiver Überwachung wird zusammen mit start/stop getestet.)

## T5 – `/honeypot start` und `stop` (Aufgabe 8)
Einspielen: `/module reload honeypot`. Der Bot braucht im Channel: Kanal ansehen, Nachrichten senden, Nachrichtenverlauf, Nachrichten verwalten,
Mitglieder bannen, @everyone erwähnen, Private Threads erstellen, In Threads senden.
1. Ohne gesetzten Channel und ohne Channel „honeypot“: `/honeypot start` → Channel „honeypot“ wird angelegt, Infonachricht erscheint mit @everyone-Ping (Test-Account bekommt Benachrichtigung).
2. `/honeypot start` erneut → „bereits aktiv“.
3. `/honeypot stop` → Infonachricht wird bearbeitet, unten steht „Honeypot under construction“. Kein neuer Ping.
4. `/honeypot stop` erneut → „bereits inaktiv“.
5. `/honeypot start` → derselbe Zusatz verschwindet, Nachricht wird bearbeitet, KEIN neuer Ping, keine zweite Nachricht.
6. `/honeypot channel channel:#test1` (bei aktiver Überwachung) → alte Infonachricht im alten Channel weg, neue mit Ping in #test1.
7. Dem Bot im Channel das Recht „Nachrichten verwalten“ entziehen, `/honeypot stop`, `/honeypot start` → Meldung, dass dieses Recht fehlt; Überwachung bleibt inaktiv.
8. Optional: Bot-Rechte wieder geben; Infonachricht von Hand löschen und `/honeypot stop` + `/honeypot start` → Nachricht kommt ohne Ping neu.
- Erwartet: wie beschrieben.

## T7 – Bann, Log-Thread und Zähler (Aufgaben 10–12)
Einspielen: `/module reload honeypot`. Du brauchst einen **Test-Account** (Zweit-Account, ohne Moderator-Recht und ohne Save-Role) – er wird wirklich gebannt (danach Bann aufheben).
Der Bot muss in der Rollenhierarchie über dem Test-Account stehen. Überwachung muss aktiv sein (`/honeypot start`).
1. Mit Test-Account im Honeypot-Channel eine Nachricht schreiben → Account ist sofort gebannt, seine Nachricht ist weg (auch Nachrichten der letzten Stunde in anderen Channels).
2. Infonachricht zeigt „Bans: 1“ (bearbeitet, kein neuer Ping).
3. Im Honeypot-Channel existiert ein privater Thread „honeypot-log“; als Moderator (mit „Threads verwalten“) sichtbar, für normale User nicht. Eintrag: User-ID, Name, Banngrund, Nachricht, Zeitpunkt.
4. Bann des Test-Accounts aufheben, ihn wieder einladen. `/honeypot setrole` mit einer Rolle des Test-Accounts, erneut schreiben → KEIN Bann.
5. Als Moderator/Admin selbst im Honeypot-Channel schreiben → KEIN Bann. `/honeypot stop` und mit Test-Account (ohne Save-Role) schreiben → KEIN Bann.
6. Test-Account mit Rolle **über** der Bot-Rolle (oder Server-Owner-Test nicht möglich) → Bann schlägt fehl: Eintrag „Bann fehlgeschlagen“ mit Fehler im Log-Thread, Zähler steigt nicht.
7. Nachricht im Log-Thread schreiben (als Moderator) → keine Reaktion.
8. Honeypot-Channel löschen → `/honeypot status`: Überwachung inaktiv, Channel nicht gesetzt.
9. Optional: Log-Thread löschen, neuen Bann auslösen → Thread wird neu angelegt.
- Erwartet: wie beschrieben.

## T6 – `/honeypot setlanguage` (Aufgabe 9)
Einspielen: `/module reload honeypot`. Voraussetzung: Überwachung aktiv (T5).
1. `/honeypot setlanguage language:` tippen → Autocomplete schlägt DEUTSCH und ENGLISH vor.
2. `language:ENGLISH` → Infonachricht im Channel wird auf Englisch bearbeitet (Bans-Zahl bleibt), kein neuer Ping, keine zweite Nachricht.
3. `language:deutsch` (klein) → wieder Deutsch. `/honeypot status` zeigt DEUTSCH.
4. `language:KLINGONISCH` → Meldung „Unbekannte Sprache“ mit Liste, nichts ändert sich.
5. Optional: In `modules/honeypot/languages.txt` einen Abschnitt `[FRANCAIS]` mit zwei Zeilen ` - …` ergänzen (ohne Reload) → erscheint sofort im Autocomplete und ist wählbar.
- Erwartet: wie beschrieben.
