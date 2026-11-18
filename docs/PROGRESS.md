STATUS: FERTIG

## Zuletzt erledigt
- Aufgaben 1–15 fertig; 119 Tests grün (`.venv/bin/pytest -q`). Nutzer-Tests T1–T8 alle OK, Abnahmekriterien des Lastenhefts bestätigt.

## Nächster Schritt
- Keiner – Projekt abgeschlossen.

## Offene Probleme
- Einrichtung (falls `.venv` neu): `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt -r requirements-dev.txt`
- `.venv` = Python 3.14, Docker = 3.13 → 3.13-kompatibel bleiben.
- Message Content Intent muss im Developer Portal aktiv sein, sonst startet der Bot nicht.
- T7.6: Bann gelang trotz erwarteter Hierarchie-Sperre (vermutlich Rolle nicht wirklich über Bot-Rolle) – kein Codefehler, vom Nutzer als unkritisch eingestuft.

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
