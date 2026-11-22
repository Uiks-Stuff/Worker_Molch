STATUS: ARBEITET

## Zuletzt erledigt
- Plan für Modul `rolepanel` (`docs/PLAN.md`, Aufgaben 1–19) erstellt und vom Nutzer freigegeben.
- Aufgaben 1–3: gemeinsamer Willkommenskanal-Dienst `core/welcome_channel.py` (Speicher, Kanalverwaltung, Anbieter-Registry,
  publish/refresh/remove/set_hierarchy/arrange/move_channel).
- Aufgabe 4: `core/errors.py` (`UserFacingCheckFailure`), Error-Handler in `main.py`, Label `manage_roles`.
- Aufgaben 5–17: Modul `modules/rolepanel/` komplett (storage, languages, views, cog mit allen 10 Befehlen, Buttons als
  `DynamicItem`, Modal für `setmessage`, Listener für gelöschte Rollen/Kanäle) + Tests. Bestand: 271 Tests grün.
- Feedback eingearbeitet: manuell gelöschte Panel-Nachricht wird neu erzeugt (Listener + start/setlanguage),
  `/rolepanel info`, Button-Farbe nach Rollenfarbe (nächstliegende der 4 Discord-Stile). Neuer Test T14.
- Aufgabe 18: README (Modul `rolepanel`) und `docs/TESTS_FUER_DICH.md` (T1–T13) geschrieben.

## Nächster Schritt
- Aufgabe 19 (manuell, Nutzer): zuerst Rebuild (T1: `cd /home/uik/projects/Worker_Molch && sudo docker compose up -d --build`),
  dann `/module enable modul:rolepanel` und T2–T13 sowie T14 (Wiederholung nach Feedback; erneuter Rebuild nötig) aus `docs/TESTS_FUER_DICH.md` durchführen; Ergebnisse in `docs/FEEDBACK.md`.
- Danach in neuer Sitzung `/weiter`: Feedback einarbeiten; bei lauter OK → STATUS: FERTIG, Modul nach `docs/archiv/` archivieren.

## Offene Probleme
- Einrichtung (falls `.venv` neu): `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt -r requirements-dev.txt`
- `.venv` = Python 3.14, Docker = 3.13 → 3.13-kompatibel bleiben.
- Hierarchie-Anordnung (T9) ist ohne zweites Modul nur eingeschränkt manuell prüfbar (durch Unit-Tests abgedeckt).

## Annahmen & Entscheidungen
- Save-Roles = Zugriff auf die `/rolepanel`-Befehle (Nutzer). Zusätzlich immer erlaubt: Servereigentümer + Administrator
  (Annahme, sonst kann niemand die erste Save-Role setzen). Kein `default_permissions`, Prüfung im Bot (`interaction_check`).
- Buttons dürfen alle Mitglieder nutzen (Nutzer). Rückmeldung sprachneutral (➕/➖); persistent über `DynamicItem`.
- Hierarchie: kleinere Zahl = weiter oben (Nutzer). Bereich 1–100, Standard 10. Bei Änderung nur Neuordnung, wenn Panel aktiv.
- `/rolepanel channel` (Nutzer): Pflichtparameter, überschreibt Kanal; Bot-Nachrichten aller Module ziehen ohne Ping um (Annahme).
- Willkommenskanal + Anordnung als gemeinsamer Dienst in `core/welcome_channel.py` (Nutzer ok, Rebuild nötig).
- Befehlsnamen klein; „setmassage“ → `setmessage`, „sethierarchie“ bleibt.
- Kein Kanal gesetzt → `start` nutzt vorhandenen „willkommen“ oder legt ihn an.
- Anordnen = falsch platzierte Bot-Nachrichten löschen und neu senden; User-Nachrichten bleiben unberührt.
- Sprachdatei: nur Zeilen mit `-` sind Text; „Rolle 1…“ = Platzhalter, Rollenliste wird automatisch angehängt.
- Eigener Text per `setmessage` gilt pro Sprache; leer oder unverändert = Standardtext. Max. 1800 Zeichen.
- `userrole` lehnt gefährliche Rollen ab (Admin-/Moderationsrechte, ≥ Bot-Rolle, ≥ eigene Rolle außer Eigentümer/Admin,
  verwaltet, @everyone). Max. 25 Rollen. Entfernen ist immer erlaubt. Beim Klick wird die Rolle erneut geprüft (ohne Nutzer-Hierarchie).
- `@everyone` pingt nur beim (Neu-)Posten durch `start`; nach `stop` + `start` wird neu gepostet und damit erneut gepingt
  (weil `stop` die Nachricht löscht – Annahme). Bearbeiten/Neuordnen/Kanalwechsel pingen nie.
- `stop` löscht die Nachricht; Kanal gelöscht → Panel inaktiv; Rolle gelöscht → aus Auswahl/Save-Roles entfernt, Panel aktualisiert.
- Speicherung `data/rolepanel.json` und `data/welcome_channel.json` pro Guild; `tests/` ist laut `.gitignore` nicht versioniert.
- `config/modules.json` wurde nicht geändert; Aktivierung per `/module enable modul:rolepanel` durch den Nutzer.
