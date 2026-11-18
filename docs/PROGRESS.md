STATUS: ARBEITET

## Zuletzt erledigt
- Plan erstellt und kritisch überarbeitet (`docs/PLAN.md`): Architektur (storage/languages/service/cog), 15 Aufgaben, A0–A7.
- Test-Setup: `requirements-dev.txt`, `pytest.ini`, `tests/test_smoke.py` (6 Tests, grün).

## Nächster Schritt
- Plan-Freigabe + Antworten auf offene Fragen abwarten. Danach Aufgabe 1 (Core-Intents in `main.py`).

## Offene Probleme
- Einrichtung (falls `.venv` neu): `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt -r requirements-dev.txt`
- `.venv` = Python 3.14, Docker = 3.13 → 3.13-kompatibel bleiben.
- Lastenheft „Daten / Speicherung“ unvollständig („setRoles und , sowie des“) → Annahme: zusätzlich Sprache speichern.
- Message Content Intent muss im Developer Portal aktiv sein, sonst startet der Bot nach Aufgabe 1 nicht.

## Annahmen & Entscheidungen
- Befehlsnamen klein (`setrole`, `removerole`, `setlanguage`) – Discord/discord.py erzwingt Kleinschreibung.
- Moderatoren/Admin = Berechtigung `ban_members` (Admin implizit); diese werden nie gebannt.
- Log-Thread privat; sichtbar für „Threads verwalten“/Admin (Discord kann keine Rolle direkt in einen Thread setzen).
- Speicherung `data/honeypot.json` pro Guild (`core/database.py` ist leer, ungenutzt).
- Rollen: `rolle1`–`rolle5`; Channel als Channel-Auswahl; Auto-Channel heißt „honeypot“ (Discord: klein).
- Standardsprache DEUTSCH; Platzhalter `X` als eigenes Wort; Sprache gilt nur für die Infonachricht, Log bleibt deutsch.
- `@everyone` pingt nur beim Neusenden der Infonachricht, Bearbeitungen pingen nicht.
- Bann löscht Nachrichten der letzten Stunde (`delete_message_seconds=3600`).
- `stop` lässt die Infonachricht stehen; Channel entfernt/gelöscht → Überwachung aus.
- Mehrere Nachrichten eines Users → nur ein Bann, Zähler +1.
