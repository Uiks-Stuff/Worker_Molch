# Worker_Molch – Arbeitsanweisung für Claude

## Projekt
- Modularer Discord-Bot: Python 3.13, discord.py 2.7.1, Betrieb per Docker Compose.
- Struktur: `main.py` (Einstieg), `core/` (Modulverwaltung), `modules/<name>/{__init__.py,cog.py}`
  (optionale Module mit `async def setup(bot)`), `config/modules.json` (aktive Module).
- Konventionen des bestehenden Codes übernehmen (deutsche Kommentare/Logmeldungen, Stil, Aufbau).
- Neue Funktionen bevorzugt als eigenes Modul unter `modules/` umsetzen, `core/` nur wenn nötig.

## Auftrag
Setze `docs/LASTENHEFT.md` eigenständig um. Der Plan steht in `docs/PLAN.md`,
der Stand in `docs/PROGRESS.md`.

## Ablauf je Aufgabe
1. Genau EINE offene Aufgabe aus PLAN.md nehmen.
2. Umsetzen.
3. Automatische Tests mit pytest schreiben und ausführen: `.venv/bin/pytest -q`.
   Discord-Objekte (Interaction, Channel, Member …) mit `unittest.mock` / `AsyncMock` nachbilden –
   niemals echte Verbindung zu Discord.
4. Fehler beheben, bis alle Tests grün sind.
5. Checkbox in PLAN.md abhaken.
6. PROGRESS.md aktualisieren (siehe unten).
7. `git add` + `git commit` mit aussagekräftiger deutscher Nachricht.

## Manuelle Tests durch den Nutzer
Alles, was nur mit dem echten Bot in Discord prüfbar ist, kommt nach `docs/TESTS_FUER_DICH.md`:
- Nummeriert (T1, T2, …), Schritt-für-Schritt, mit erwartetem Ergebnis.
- Angeben, wie der Nutzer die Änderung einspielt:
  - nur Dateien in `modules/` geändert → in Discord `/module reload <name>` (bzw. `/module enable`)
  - `main.py`, `core/`, `requirements.txt`, `Dockerfile` geändert →
    `cd /home/uik/projects/Worker_Molch && sudo docker compose up -d --build`
- Danach mit anderen Aufgaben weitermachen statt zu warten.
- Sind nur noch Aufgaben offen, die Nutzer-Feedback brauchen: in PROGRESS.md die Zeile
  `STATUS: WARTE_AUF_FEEDBACK` setzen und die Sitzung beenden.

## PROGRESS.md (kurz halten, max. ca. 60 Zeilen)
- `STATUS: ARBEITET` | `STATUS: WARTE_AUF_FEEDBACK` | `STATUS: FERTIG`
- Zuletzt erledigt
- Nächster Schritt (so konkret, dass eine neue Sitzung sofort weitermachen kann)
- Offene Probleme
- Annahmen & Entscheidungen (Unklarheiten im Lastenheft: sinnvolle Annahme treffen, hier notieren)

## Token sparen
- Zu Beginn nur PROGRESS.md und PLAN.md lesen; LASTENHEFT.md nur, wenn für die Aufgabe nötig.
- Nur die Dateien lesen, die für die aktuelle Aufgabe relevant sind.
- Keine langen Zusammenfassungen im Chat – das Wichtige gehört in PROGRESS.md.

## Verboten
- `.env` lesen oder ändern (enthält den Bot-Token). Geheimnisse nie in Code, Tests oder Commits.
- `git push`, `sudo`, `docker` – Deployment und Push macht der Nutzer.
- Bestehende Funktionen (/ping, /module, /clear) kaputt machen – vorhandene Tests müssen grün bleiben.
