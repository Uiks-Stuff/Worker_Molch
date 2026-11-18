STATUS: ARBEITET

## Zuletzt erledigt
- Plan erstellt und kritisch überarbeitet (`docs/PLAN.md`): Architektur (storage/languages/service/cog), 15 Aufgaben, A0–A7.
- Test-Setup: `requirements-dev.txt`, `pytest.ini`, `tests/test_smoke.py` (6 Tests, grün).

- Aufgabe 1: Intents `guild_messages` + `message_content`, Label `ban_members` (T1 offen, braucht Rebuild).

- Aufgabe 2: `modules/honeypot/storage.py` (`HoneypotStorage.load/save/update`), 8 Tests.

- Aufgabe 3: `languages.txt` (DEUTSCH, ENGLISH), `languages.py` (`get_language`, `resolve_language`, `render_info`), 11 Tests.

## Nächster Schritt
- Aufgabe 4 (`cog.py` GroupCog + `/honeypot status`, Smoke-Test Extension laden).

## Offene Probleme
- Einrichtung (falls `.venv` neu): `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt -r requirements-dev.txt`
- `.venv` = Python 3.14, Docker = 3.13 → 3.13-kompatibel bleiben.
- Lastenheft „Daten / Speicherung“ unvollständig („setRoles und , sowie des“) → Annahme: zusätzlich Sprache speichern.
- Message Content Intent muss im Developer Portal aktiv sein, sonst startet der Bot nach Aufgabe 1 nicht.

## Annahmen & Entscheidungen
- Befehlsnamen klein (`setrole`, `removerole`, `setlanguage`) – Discord/discord.py erzwingt Kleinschreibung.
- Moderatoren/Admin = Berechtigung `ban_members` (Nutzer bestätigt); diese werden nie gebannt.
- Log-Thread privat; sichtbar für „Threads verwalten“/Admin, keine eigene Log-Rolle (Nutzer bestätigt).
- Speicherung `data/honeypot.json` pro Guild (`core/database.py` ist leer, ungenutzt).
- Rollen: `rolle1`–`rolle5`; Channel als Channel-Auswahl.
- `start` ohne Channel: vorhandenen Channel „honeypot“ nutzen, sonst anlegen (Nutzer bestätigt).
- Standardsprache DEUTSCH; Platzhalter `X` als eigenes Wort; Sprache gilt nur für die Infonachricht, Log bleibt deutsch.
- `@everyone` pingt einmalig beim Aufsetzen; nicht nach Neustart, beim Bearbeiten oder wenn Nachricht existiert (Nutzer bestätigt).
  Gelöschte Infonachricht wird ohne Ping neu gesendet.
- Bann sofort, danach Honeypot-Nachricht sofort löschen (Nutzer). Zusätzlich `delete_message_seconds=3600`
  (entfernt Spam des Users der letzten Stunde serverweit) (Nutzer bestätigt).
- `stop`: Infonachricht bekommt Zusatz aus Zeile 3 der Sprachdatei (Standard „Honeypot under construction“) (Nutzer).
- Infonachricht wird erst bei `start` gepostet, nicht schon bei `/honeypot channel` im inaktiven Zustand. (Nutzer bestätigt)
- Channel entfernt/gelöscht → Überwachung aus.
- Mehrere Nachrichten eines Users → nur ein Bann, Zähler +1.
