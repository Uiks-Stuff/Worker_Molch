---
name: plan
description: Lastenheft analysieren und einen Umsetzungsplan in docs/PLAN.md erstellen
---
1. Lies docs/LASTENHEFT.md vollständig sowie README.md und die Dateien in core/ und modules/,
   um die bestehende Architektur zu verstehen.
2. Prüfe die Testumgebung: Gibt es `.venv/`? Wenn nicht, lege `requirements-dev.txt` an
   (pytest, pytest-asyncio) und notiere in PROGRESS.md, welche Befehle der Nutzer zur Einrichtung
   ausführen muss. Schreibe erste Tests für den bestehenden Code (Smoke-Tests), falls noch keine existieren.
3. Leite die Anforderungen ab und nummeriere sie (A1, A2, …). Unklares als Annahme kennzeichnen.
4. Schreibe docs/PLAN.md: kleine, einzeln testbare Aufgaben als Checkboxen `- [ ]`,
   jeweils mit Verweis auf die Anforderung und einem Abnahmekriterium.
   Aufgaben, die nur der Nutzer prüfen kann, mit `(manuell)` markieren.
5. Lege docs/PROGRESS.md an (Aufbau siehe CLAUDE.md), `STATUS: ARBEITET`.
6. Committe.
7. Fasse den Plan in wenigen Sätzen zusammen und nenne offene Fragen an mich.
   Beginne NICHT mit der Umsetzung, bis ich den Plan freigebe.
