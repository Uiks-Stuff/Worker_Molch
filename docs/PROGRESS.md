STATUS: ARBEITET

## Zuletzt erledigt
- Plan für Modul `rolepanel` erstellt (`docs/PLAN.md`, Aufgaben 1–19). Bestand: 119 Tests grün.

## Nächster Schritt
- Warten auf Freigabe des Plans durch den Nutzer (offene Fragen siehe unten), dann Aufgabe 1:
  `core/welcome_channel.py` – Speicherklasse für `data/welcome_channel.json` + Tests.

## Offene Probleme
- Einrichtung (falls `.venv` neu): `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt -r requirements-dev.txt`
- `.venv` = Python 3.14, Docker = 3.13 → 3.13-kompatibel bleiben.
- Offene Fragen an den Nutzer (Antworten hier eintragen bzw. Annahmen bestätigen):
  1. Was sind „Save-Roles“ beim Rollenpanel? (Annahme: nur Mitglieder mit Save-Role dürfen Buttons nutzen, wenn welche gesetzt sind.)
  2. Hierarchie: kleinere Zahl weiter oben? (Annahme: ja.)
  3. Zusätzlich `/rolepanel channel` (Kanal wählen) und `/rolepanel status`? (Annahme: nein, nicht im Lastenheft.)
  4. Gemeinsamer Willkommenskanal in `core/` (einmal Rebuild nötig) – ok?

## Annahmen & Entscheidungen
- Befehlsnamen klein; „setmassage“ → `setmessage`, „sethierarchie“ bleibt.
- Moderatoren/Admins = Berechtigung „Rollen verwalten“ (`manage_roles`).
- Willkommenskanal + Anordnung als gemeinsamer Dienst in `core/welcome_channel.py` (für künftige Module, F4).
- Kein Kanal gesetzt → `start` nutzt vorhandenen „willkommen“ oder legt ihn an (Discord schreibt Kanalnamen klein).
- Anordnen = falsch platzierte Bot-Nachrichten löschen und neu senden; User-Nachrichten bleiben unberührt.
- Sprachdatei: nur Zeilen mit `-` sind Text; „Rolle 1…“ = Platzhalter, Rollenliste wird automatisch angehängt.
- Eigener Text per `setmessage` gilt pro Sprache; leeres Feld = Standardtext. Eingabe per Modal.
- `userrole` lehnt gefährliche Rollen ab (Admin-/Moderationsrechte, ≥ Bot-Rolle, ≥ eigene Rolle, verwaltet, @everyone). Max. 25 Rollen.
- Button-Rückmeldung sprachneutral (➕/➖); Buttons persistent über `DynamicItem`.
- `@everyone` pingt nur beim ersten Posten (wie Honeypot).
- Speicherung `data/rolepanel.json` und `data/welcome_channel.json` pro Guild; `tests/` ist laut `.gitignore` nicht versioniert.
