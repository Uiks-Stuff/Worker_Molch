STATUS: ARBEITET

## Zuletzt erledigt
- Plan für Modul `rolepanel` erstellt (`docs/PLAN.md`, Aufgaben 1–19) und nach Nutzer-Antworten angepasst; vom Nutzer freigegeben.
- Aufgabe 1: `core/welcome_channel.py` (`WelcomeChannelStorage`) + Tests. 
- Aufgabe 2: `WelcomeChannelManager` (get/set/ensure_channel, handle_channel_deleted, `get_welcome_manager`) + Tests. Bestand: 132 Tests grün.
- Aufgabe 3: Anbieter-Registry, publish/refresh/remove/set_hierarchy/arrange/move_channel + Tests. Bestand: 148 Tests grün.
- Aufgabe 4: `core/errors.py`, Error-Handler in `main.py` (UserFacingCheckFailure, Label manage_roles) + Tests; T1 eingetragen (Rebuild nötig). 153 Tests grün.

## Nächster Schritt
- Aufgabe 5: `modules/rolepanel/__init__.py`, `storage.py` + Tests (Details in PLAN.md).

## Offene Probleme
- Einrichtung (falls `.venv` neu): `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt -r requirements-dev.txt`
- `.venv` = Python 3.14, Docker = 3.13 → 3.13-kompatibel bleiben.

## Annahmen & Entscheidungen
- Save-Roles = Zugriff auf die `/rolepanel`-Befehle (Nutzer). Zusätzlich immer erlaubt: Servereigentümer + Administrator
  (Annahme, sonst kann niemand die erste Save-Role setzen). Daher kein `default_permissions`, Prüfung im Bot.
- Buttons dürfen alle Mitglieder nutzen (Nutzer).
- Hierarchie: kleinere Zahl = weiter oben (Nutzer). Bereich 1–100, Standard 10.
- `/rolepanel channel` zusätzlich (Nutzer): Pflichtparameter, überschreibt gesetzten Kanal; Bot-Nachrichten aller registrierten
  Module ziehen ohne Ping in den neuen Kanal um (Annahme). Kein `/rolepanel status` (nur `channel` gewünscht).
- Willkommenskanal + Anordnung als gemeinsamer Dienst in `core/welcome_channel.py` (Nutzer ok, Rebuild nötig).
  `core/errors.py` → `UserFacingCheckFailure`, deren Text der Error-Handler in `main.py` anzeigt.
- Befehlsnamen klein; „setmassage“ → `setmessage`, „sethierarchie“ bleibt.
- Kein Kanal gesetzt → `start` nutzt vorhandenen „willkommen“ oder legt ihn an (Discord schreibt Kanalnamen klein).
- Anordnen = falsch platzierte Bot-Nachrichten löschen und neu senden; User-Nachrichten bleiben unberührt.
- Sprachdatei: nur Zeilen mit `-` sind Text; „Rolle 1…“ = Platzhalter, Rollenliste wird automatisch angehängt.
- Eigener Text per `setmessage` gilt pro Sprache; leeres Feld = Standardtext. Eingabe per Modal.
- `userrole` lehnt gefährliche Rollen ab (Admin-/Moderationsrechte, ≥ Bot-Rolle, ≥ eigene Rolle außer Eigentümer/Admin,
  verwaltet, @everyone). Max. 25 Rollen.
- Button-Rückmeldung sprachneutral (➕/➖); Buttons persistent über `DynamicItem`.
- `@everyone` pingt nur beim ersten Posten (wie Honeypot).
- Speicherung `data/rolepanel.json` und `data/welcome_channel.json` pro Guild; `tests/` ist laut `.gitignore` nicht versioniert.
