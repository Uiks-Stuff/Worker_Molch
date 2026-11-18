STATUS: ARBEITET

## Zuletzt erledigt
- Plan erstellt (`docs/PLAN.md`), Testumgebung geprüft: `.venv` mit pytest/pytest-asyncio vorhanden.
- `requirements-dev.txt`, `pytest.ini`, `tests/test_smoke.py` (6 Smoke-Tests, grün) angelegt.

## Nächster Schritt
- Plan-Freigabe des Nutzers abwarten. Danach Aufgabe 1 aus PLAN.md (Core: Intents + Error-Label).

## Offene Probleme
- Einrichtung (falls `.venv` neu): `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt -r requirements-dev.txt`
- `.venv` nutzt Python 3.14, Docker 3.13 – auf 3.13-kompatiblen Code achten.
- `docs/LASTENHEFT.md` hat unfertigen Satz in „Daten / Speicherung“ („Speicherung der setRoles und , sowie des“) → Annahme unten.

## Annahmen & Entscheidungen
- Moderatoren/Admin = Berechtigung `ban_members` (Administrator hat sie implizit); gleiche Gruppe wird nie gebannt.
- Thread: privat, sichtbar für „Threads verwalten“/Admin; keine einzelnen Rollen hinzufügen.
- Message Content Intent nötig, um „Nachricht“ im Log zu speichern (muss im Developer Portal aktiviert werden); ohne Inhalt: Hinweistext.
- Speicherung: `data/honeypot.json` pro Guild (`core/database.py` ist leer, wird nicht genutzt).
- Rollen-Listen: `rolle1`–`rolle5`-Parameter; Channel-Parameter als Channel-Auswahl.
- Standardsprache DEUTSCH; Sprachdatei `modules/honeypot/languages.txt` (zusätzlich Beispiel ENGLISH).
- `@everyone` in der Infonachricht pingt nur beim ersten Senden, Bearbeitungen pingen nicht.
- Beim Ban werden Nachrichten der letzten Stunde des Users gelöscht (`delete_message_seconds=3600`).
- Wird der Channel entfernt/gelöscht, wird die Überwachung gestoppt.
