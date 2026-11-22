# Manuelle Tests für dich

Claude trägt hier Tests ein, die nur mit dem echten Bot in Discord prüfbar sind.
Ergebnisse bitte in `FEEDBACK.md` eintragen.

## T1 – Core-Änderung (Willkommenskanal-Dienst, Fehlerbehandlung)
Einspielen (Core geändert): `cd /home/uik/projects/Worker_Molch && sudo docker compose up -d --build`
1. Warten, bis der Bot online ist.
2. `/ping` ausführen → Erwartet: „Pong! Latenz: … ms“.
3. `/honeypot status` ausführen → Erwartet: Statusanzeige wie bisher, keine Fehlermeldung.
4. `/module list` ausführen → Erwartet: Modulliste wie bisher.

## Vorbereitung für T2–T13
- Bot-Rolle muss **Rollen verwalten** haben und in der Rollenliste **über** den Test-Rollen stehen.
- Lege zwei harmlose Test-Rollen an (z. B. „Test-A“, „Test-B“, ohne Sonderrechte) und eine Rolle „Test-Mod“ mit dem Recht „Nachrichten verwalten“.
- Zweites Konto/Freund ohne Admin-Rechte als „normales Mitglied“ bereithalten.
- Modul einspielen (nur `modules/`): in Discord `/module enable modul:rolepanel` (bzw. `/module reload modul:rolepanel`).

## T2 – Zugriff (Save-Roles)
1. Als normales Mitglied `/rolepanel start` → Erwartet: Meldung „Dafür brauchst du eine Save-Role …“.
2. Als Admin/Eigentümer `/rolepanel setrole rolle1:@Test-Mod` → Erwartet: „Hinzugefügt: @Test-Mod“.
3. Als normales Mitglied mit Test-Mod: `/rolepanel start` → Erwartet: keine Zugriffsmeldung (Fehlermeldung „keine wählbaren Rollen“ ist ok).
4. Als Admin `/rolepanel setrole rolle1:@everyone` → Erwartet: „Nicht erlaubt“.
5. `/rolepanel removerole rolle1:@Test-Mod` → Erwartet: „Entfernt“; danach hat das Mitglied wieder keinen Zugriff.

## T3 – Wählbare Rollen
1. `/rolepanel userrole rolle1:@Test-A rolle2:@Test-B` → Erwartet: „Hinzugefügt: …“.
2. `/rolepanel userrole rolle1:@Test-Mod` → Erwartet: „Nicht erlaubt … Nachrichten verwalten“.
3. `/rolepanel userrole rolle1:@Test-B` (nochmal) → Erwartet: „Entfernt: @Test-B“; mit erneutem Aufruf wieder hinzufügen.
4. Rolle über der Bot-Rolle versuchen → Erwartet: „liegt nicht unter meiner höchsten Rolle“.

## T4 – start / Willkommenskanal
1. Ohne Kanal „willkommen“ und ohne gesetzten Kanal: `/rolepanel start` → Erwartet: Kanal „willkommen“ wird angelegt, Nachricht mit deutschem Text, Rollenliste (Erwähnungen) und je einem Button; **@everyone wird gepingt**.
2. Nochmal `/rolepanel start` → Erwartet: „bereits aktiv“.

## T5 – Buttons
1. Als normales Mitglied auf „Test-A“ klicken → Erwartet: nur für dich sichtbar „➕ @Test-A“, Rolle ist vergeben.
2. Erneut klicken → „➖ @Test-A“, Rolle entfernt.
3. Bot neu starten (`sudo docker compose restart`) bzw. `/module reload modul:rolepanel`, danach Button klicken → Erwartet: funktioniert weiterhin.
4. Rolle „Test-B“ per Serverrechten die Bot-Rolle übersteigen lassen und klicken → Erwartet: verständliche Meldung „Ich darf … nicht vergeben“.

## T6 – Sprache
1. `/rolepanel setlanguage language:english` → Erwartet: Nachricht im Kanal wird sofort englisch (kein neuer Ping, gleiche Nachricht).
2. `/rolepanel setlanguage language:xyz` → Erwartet: „Unbekannte Sprache“ mit Liste.
3. In `modules/rolepanel/languages.txt` einen Abschnitt `[ESPANOL]` mit Zeile ` - …` ergänzen → Autocomplete zeigt ihn ohne Reload.

## T7 – Eigener Text
1. `/rolepanel setmessage` → Erwartet: Formular, vorbefüllt mit dem aktuellen Text der Sprache.
2. Text ändern, absenden → Erwartet: Nachricht im Kanal zeigt den neuen Text (Rollenliste bleibt).
3. Sprache wechseln und zurück → Erwartet: eigener Text gilt nur für die jeweilige Sprache.
4. Formular leeren und absenden → Erwartet: Standardtext.

## T8 – Rollen ändern bei aktivem Panel
1. `/rolepanel userrole` mit einer weiteren Rolle → Erwartet: Nachricht aktualisiert (neuer Button).
2. Eine wählbare Rolle in den Servereinstellungen löschen → Erwartet: Button verschwindet, Rolle ist aus der Auswahl entfernt.
3. `/rolepanel clear` → Erwartet: Nachricht bleibt ohne Buttons stehen.

## T9 – Hierarchie / Anordnung
Benötigt einen zweiten Anbieter; ersatzweise nur Wert prüfen:
1. `/rolepanel sethierarchie ebene:50` → Erwartet: Bestätigung; `ebene:0` bzw. `101` wird von Discord abgelehnt.
2. Eigene Nachricht eines Mitglieds im Kanal bleibt nach dem Befehl unangetastet.

## T10 – Kanal wechseln
1. Zweiten Textkanal anlegen. `/rolepanel channel channel:#neu` → Erwartet: Nachricht im alten Kanal gelöscht, im neuen gepostet (ohne Ping), Buttons funktionieren.
2. Gleichen Kanal nochmal → „bereits der Willkommenskanal“.
3. Kanal, in dem der Bot nicht schreiben darf → Erwartet: Meldung mit fehlenden Rechten.

## T11 – stop
1. `/rolepanel stop` → Erwartet: Nachricht entfernt. Nochmal → „nicht aktiv“.
2. `/rolepanel start` → Erwartet: Nachricht wird neu gepostet.

## T12 – Robustheit
1. Panel-Nachricht manuell löschen, dann `/rolepanel setlanguage language:deutsch` → Erwartet: Nachricht wird ohne Ping neu gesendet.
2. Willkommenskanal löschen → Erwartet: Rollenauswahl inaktiv; `/rolepanel start` legt/wählt Kanal neu.

## T13 – Regression
1. `/ping`, `/clear`, `/module list`, `/honeypot status` funktionieren wie vorher.
