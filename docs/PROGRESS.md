STATUS: ARBEITET

## Zuletzt erledigt
- Aufgaben 1–14 fertig, 119 Tests grün (`.venv/bin/pytest -q`), alles committed.
- Core: Intents `guild_messages` + `message_content`, Label `ban_members` (`main.py`).
- Modul `modules/honeypot/`: `storage.py`, `languages.py` + `languages.txt`, `service.py` (Infonachricht, Bann, Log-Thread, Zähler), `cog.py` (7 Befehle + Listener).
- README um Modul `honeypot` ergänzt; `docs/TESTS_FUER_DICH.md` mit T1–T8.

## Nächster Schritt
- Aufgabe 15 (manuell, Nutzer): T1–T8 aus `docs/TESTS_FUER_DICH.md` in Discord durchführen, Ergebnisse in `docs/FEEDBACK.md` eintragen.
  Reihenfolge der Einspielung: Message Content Intent im Developer Portal aktivieren → Rebuild (T1) → `/module enable honeypot` → T2…
- Danach in neuer Sitzung `/weiter`: Feedback einarbeiten (Skill `feedback`), bei allem OK → `STATUS: FERTIG`.

## Offene Probleme
- Einrichtung (falls `.venv` neu): `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt -r requirements-dev.txt`
- `.venv` = Python 3.14, Docker = 3.13 → 3.13-kompatibel bleiben.
- Message Content Intent muss im Developer Portal aktiv sein, sonst startet der Bot nicht.
- Nichts davon wurde gegen echtes Discord geprüft (nur Mocks); Annahmen zu discord.py-Verhalten (z. B. privater Thread, `delete_message_seconds`) sind durch T7 zu bestätigen.

## Annahmen & Entscheidungen
- Befehlsnamen klein (`setrole`, `removerole`, `setlanguage`) – Discord/discord.py erzwingt Kleinschreibung.
- Moderatoren/Admin = Berechtigung `ban_members` oder `administrator`; diese und der Servereigentümer werden nie gebannt (Nutzer bestätigt).
- Log-Thread privat („honeypot-log“, `invitable=False`); sichtbar für „Threads verwalten“/Admin, keine eigene Log-Rolle (Nutzer bestätigt).
- Speicherung `data/honeypot.json` pro Guild (`core/database.py` ist leer, ungenutzt); Lastenheft „Daten / Speicherung“ unvollständig → zusätzlich Sprache, Infonachricht-ID, Thread-ID gespeichert.
- Rollen: `rolle1`–`rolle5`; Channel als Channel-Auswahl; `@everyone` und Integrationsrollen werden als Save-Role abgelehnt.
- `start` ohne Channel: vorhandenen Channel „honeypot“ nutzen, sonst anlegen (Nutzer bestätigt).
- Standardsprache DEUTSCH; Platzhalter `X` als eigenes Wort; Sprache gilt nur für die Infonachricht, Log bleibt deutsch.
- `@everyone` pingt einmalig beim Aufsetzen; nicht nach Neustart, beim Bearbeiten oder wenn Nachricht existiert (Nutzer bestätigt).
  Gelöschte Infonachricht wird ohne Ping neu gesendet.
- Bann sofort, danach Honeypot-Nachricht löschen (Nutzer). Zusätzlich `delete_message_seconds=3600` (Nutzer bestätigt).
- `stop`: Infonachricht bekommt Zusatz aus Zeile 3 der Sprachdatei (Standard „Honeypot under construction“) (Nutzer).
- Infonachricht wird erst bei `start` gepostet, nicht schon bei `/honeypot channel` im inaktiven Zustand (Nutzer bestätigt).
- Channel entfernt/gelöscht → Überwachung aus.
- Mehrere Nachrichten eines Users → nur ein Bann, Zähler +1; derselbe User wird 60 s lang nicht erneut behandelt (auch nach fehlgeschlagenem Bann).
