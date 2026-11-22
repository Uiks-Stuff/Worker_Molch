# Plan: Modul `rolepanel` (Rollenauswahl per Button im Willkommenskanal)

Quelle: `docs/LASTENHEFT.md`. Tests: `.venv/bin/pytest -q` (`tests/`, Mocks mit `spec=discord.…`, keine Discord-Verbindung).

## Architektur
- **Gemeinsamer Willkommenskanal in `core/welcome_channel.py`** (Begründung: F4 verlangt, dass künftige Module in denselben
  Kanal posten und der Bot alle Nachrichten nach Hierarchieebene sortiert – das darf nicht vom Modul `rolepanel` abhängen).
  - Speicher `data/welcome_channel.json` pro Guild: `channel_id`, `posts: {schlüssel: {message_id, hierarchy}}`.
  - Module melden sich als „Anbieter“ an (`register(schlüssel, render)` in `cog_load`, `unregister` in `cog_unload`);
    `render(guild)` liefert Text + View. Die Registry hängt am Bot und überlebt `/module reload`.
  - API: `get_channel`, `set_channel`, `ensure_channel` (Fallback „willkommen“), `publish`, `refresh`, `remove`, `arrange`.
  - Core-Änderung ⇒ einmal `sudo docker compose up -d --build` nötig.
- **Modul `modules/rolepanel/`**:
  - `storage.py` – `data/rolepanel.json` pro Guild: `active`, `save_role_ids`, `user_role_ids`, `language`,
    `custom_messages {SPRACHE: text}`, `hierarchy` (Standard 10). Atomar schreiben wie Honeypot.
  - `languages.py` + `languages.txt` – Sprachdatei (eigene Kopie des Parsers, Module bleiben unabhängig).
  - `views.py` – `discord.ui.DynamicItem` mit `custom_id` `rolepanel:role:<role_id>` → Buttons funktionieren nach Neustart/Reload.
  - `cog.py` – `GroupCog` `/rolepanel` + Listener, `async def setup(bot)`.

## Anforderungen
- A1 (Rahmen): Eigenes Modul `rolepanel`, Befehlsgruppe `/rolepanel`, nur auf Servern, Antworten ephemeral.
  Moderatoren/Admins = Berechtigung **Rollen verwalten** (`manage_roles`) *(Annahme)*.
  Discord erzwingt kleine Befehlsnamen: `setrole`, `removerole`, `setlanguage`, `setmessage` (Lastenheft: „setmassage“ = Tippfehler, *Annahme*), `sethierarchie`.
- A2 (F4, Daten): Ein Willkommenskanal pro Server, gemeinsam für alle Module. Ist keiner gesetzt, nutzt `start` einen
  vorhandenen Textkanal „willkommen“ (Groß/Klein egal) oder legt ihn an.
- A3 (F4): Hierarchieebene je Modul (Standard 10, Bereich 1–100). Bot-Nachrichten registrierter Module im Willkommenskanal
  werden danach angeordnet: **kleinere Zahl = weiter oben** *(Annahme)*. Da Discord Nachrichten nicht verschieben kann,
  werden falsch platzierte Nachrichten gelöscht und in richtiger Reihenfolge neu gesendet (ohne Ping).
  Fremde Nachrichten (User) werden nie angefasst.
- A4 (Daten): Persistenz von Save-Roles, Willkommenskanal, wählbaren Rollen (userroles), Panel-Nachricht (ID + eigener Text), Sprache, Hierarchie.
  Zustand überlebt Neustart und `/module reload`.
- A5 (Rahmen): Sprachdatei `[NAME]` + Zeilen ` - …` = Nachrichtentext (mehrzeilig möglich); Zeilen ohne `-` (z. B. „Rolle 1“)
  sind nur Platzhalter und werden ignoriert – die Liste der wählbaren Rollen hängt der Bot automatisch an (eine Rolle pro Zeile,
  als Erwähnung ohne Ping). Beliebig erweiterbar, Name case-insensitive, Standard DEUTSCH, entfernte Sprache → Fallback DEUTSCH.
- A6 (F1): `/rolepanel userrole` schaltet Rollen in der Auswahl an/aus (`rolle1` Pflicht, `rolle2`–`rolle5` optional, je Rolle umschalten);
  `/rolepanel clear` leert die Auswahl. Max. 25 Rollen (Discord-Limit Buttons pro Nachricht).
  Abgelehnt werden *(Annahme, Schutz vor Rechteausweitung)*: `@everyone`, von Integrationen/Bots verwaltete Rollen,
  Rollen ≥ höchste Bot-Rolle, Rollen ≥ höchste Rolle des Ausführenden (außer Servereigentümer) sowie Rollen mit
  Admin-/Moderationsrechten (Administrator, Server/Rollen/Kanäle verwalten, Bannen, Kicken, Nachrichten verwalten, @everyone erwähnen).
- A7 (Save-Roles): `/rolepanel setrole` / `removerole` (`rolle1`–`rolle5`) verwalten gespeicherte „Save-Roles“.
  **Bedeutung unklar** – *Annahme bis zur Klärung:* Ist mindestens eine Save-Role gesetzt, dürfen nur Mitglieder mit einer
  Save-Role die Buttons nutzen; ohne Save-Roles darf jeder. (Nur Aufgabe 12 hängt davon ab.)
- A8 (F2): Klick auf einen Button gibt dem Klickenden die Rolle, erneuter Klick entfernt sie. Rückmeldung ephemeral und
  sprachneutral (`➕ @Rolle` / `➖ @Rolle`). Fehler (Rolle gelöscht/nicht mehr wählbar, Bot-Rechte/Hierarchie) verständlich melden.
- A9 (F3): Standardnachricht aus der Sprachdatei; `/rolepanel setmessage` öffnet ein Formular (Modal), vorbefüllt mit dem aktuellen Text,
  und speichert einen eigenen Text für die **aktuell gesetzte Sprache** *(Annahme)*; leeres Feld = zurück zum Standard.
- A10: `/rolepanel start` postet das Panel (Fehler, wenn keine wählbaren Rollen gesetzt sind; prüft Bot-Rechte);
  `/rolepanel stop` entfernt die Nachricht. `@everyone` pingt nur beim ersten Posten, nie beim Bearbeiten/Neuordnen *(Annahme wie Honeypot)*.
- A11: `/rolepanel setlanguage` (Autocomplete) passt die Nachricht im Kanal sofort an.
- A12 (Robustheit): gelöschte Rolle → aus Auswahl/Save-Roles entfernen + Panel aktualisieren; gelöschter Kanal → Panel inaktiv,
  Verweise zurücksetzen; manuell gelöschte Panel-Nachricht → beim nächsten Update ohne Ping neu senden.

## Aufgaben
- [ ] **1. Willkommenskanal-Speicher (A2/A4)**: `core/welcome_channel.py` – Speicherklasse für `data/welcome_channel.json`
  (Defaults, laden/speichern pro Guild, atomar).
  *Abnahme:* Tests: fehlende/defekte Datei → Defaults, Roundtrip, Guilds getrennt, `data/` wird angelegt.
- [ ] **2. Kanalverwaltung (A2/A12)**: `WelcomeChannelManager.get_channel/set_channel/ensure_channel` (vorhandenen „willkommen“
  nutzen, sonst anlegen; `Forbidden` weiterreichen), `handle_channel_deleted` (Kanal + Post-IDs zurücksetzen); Zugriff über
  `get_welcome_manager(bot)` (hängt eine Instanz an den Bot, bleibt bei Modul-Reload erhalten).
  *Abnahme:* Tests: gesetzt / vorhanden (Groß/Klein) / neu angelegt / gelöschter Kanal-ID → Fallback, Kanal gelöscht, gleiche Instanz bei 2 Aufrufen.
- [ ] **3. Posten + Anordnen (A3/A10/A12)**: Anbieter-Registry (`register`/`unregister`), `publish(guild, key, hierarchy, ping=False)`,
  `refresh` (Text/View bearbeiten; `NotFound` → ohne Ping neu senden), `remove`, `set_hierarchy`, `arrange` (Ist-Reihenfolge nach
  Message-ID vs. Soll nach (hierarchy, key); ab erster Abweichung löschen + neu senden, IDs speichern; nicht registrierte Anbieter bleiben unangetastet).
  *Abnahme:* Tests: erstes Posten mit/ohne Ping, Bearbeiten ohne Ping, NotFound → neu, remove, Reihenfolge 5/10/20 bei verschiedener
  Ankunft, gleiche Ebene stabil, bereits richtig → keine API-Aufrufe, HTTP-Fehler werden geloggt statt geworfen.
- [ ] **4. Core einbinden (A1)**: `main.py`: Label `manage_roles: "Rollen verwalten"` im Error-Handler; Manager beim Bot-Start verfügbar.
  *Abnahme:* bestehende Tests grün + Test für Label; T1 in TESTS_FUER_DICH (Rebuild, `/ping` und `/honeypot status` funktionieren weiter).
- [ ] **5. Rolepanel-Speicher (A4)**: `modules/rolepanel/__init__.py`, `storage.py` (Felder siehe Architektur, Hierarchie Standard 10).
  *Abnahme:* Tests: Defaults, Roundtrip, Guilds getrennt, unbekannter Schlüssel → Fehler.
- [ ] **6. Sprachdatei (A5)**: `languages.txt` mit `[DEUTSCH]` (Text aus Lastenheft), `[ENGLISH]`, `[FRANCAIS]`; Parser (nur `-`-Zeilen),
  `resolve_language` mit Fallback, `render_panel(text, roles)` (Text + Leerzeile + Rollen als Erwähnungen).
  *Abnahme:* Tests: Lastenheft-Beispiel inkl. „Rolle 1…“-Platzhalter, mehrzeilig, Kleinschreibung, leerer Abschnitt, Fallback, keine Rollen.
- [ ] **7. Gerüst (A1)**: `cog.py` mit `GroupCog` `/rolepanel` (`guild_only`, `default_permissions` + `checks.has_permissions(manage_roles=True)`),
  alle 9 Befehle als Platzhalter, `setup(bot)`, Anmeldung als Anbieter `rolepanel` beim Laden/Abmelden beim Entladen.
  *Abnahme:* Tests: Befehlsnamen klein und vollständig, Rechte-Dekoratoren, Extension lädt (Smoke), Registry an/ab.
- [ ] **8. `setrole` / `removerole` (A7)**: speichern/entfernen, Duplikate und nicht gesetzte Rollen melden, `@everyone`/verwaltete Rollen ablehnen.
  *Abnahme:* Tests hinzufügen, entfernen, Duplikate, Ablehnungen.
- [ ] **9. `userrole` / `clear` (A6)**: umschalten mit Prüfungen laut A6, Limit 25; bei aktivem Panel Nachricht aktualisieren
  (nach `clear` bleibt das Panel ohne Buttons stehen *(Annahme)*).
  *Abnahme:* Tests: hinzufügen, entfernen, gemischt, jede Ablehnungsregel, Limit, clear, Panel-Update nur wenn aktiv.
- [ ] **10. Buttons (A8)**: `views.py` – `DynamicItem` (Label = Rollenname, max. 80 Zeichen), Registrierung via `bot.add_dynamic_items`
  in `cog_load` / Entfernen in `cog_unload`; `render(guild)` baut Text + View aus Speicher und Sprache.
  *Abnahme:* Tests: custom_id-Format, View aus gespeicherten Rollen (gelöschte ausgelassen), Reihenfolge, 25er-Grenze.
- [ ] **11. Button-Klick (A8)**: Rolle geben/entfernen (`reason` gesetzt), Rückmeldung ephemeral; Rolle nicht mehr wählbar/gelöscht,
  `Forbidden`/Hierarchie → verständliche Meldung, Fehler loggen.
  *Abnahme:* Tests: hinzufügen, entfernen, nicht mehr in Auswahl, gelöscht, Forbidden, Panel einer anderen Guild.
- [ ] **12. Wirkung der Save-Roles (A7)** – *abhängig von deiner Antwort zu Frage 1*: laut Annahme Button nur mit Save-Role, wenn welche gesetzt sind.
  *Abnahme:* Tests: keine Save-Roles → jeder; mit Save-Roles → nur Berechtigte, Rest bekommt Hinweis.
- [ ] **13. `start` / `stop` (A2/A10)**: start: Fehler ohne wählbare Rollen; Kanal per `ensure_channel`; Bot-Rechte prüfen
  (Kanal ansehen, Nachrichten senden, Verlauf lesen, @everyone erwähnen, Rollen verwalten) → fehlende verständlich melden;
  aktiv setzen + `publish` (Ping nur beim ersten Mal) + anordnen. stop: `remove`, inaktiv. „bereits aktiv/inaktiv“ melden.
  *Abnahme:* Tests: ohne Rollen, Kanal gesetzt / „willkommen“ vorhanden / neu angelegt, Forbidden beim Anlegen, fehlende Rechte, stop, doppelt.
- [ ] **14. `setlanguage` (A11)**: Autocomplete aus Sprachdatei, speichern, aktives Panel aktualisieren.
  *Abnahme:* Tests: gültig (klein geschrieben), ungültig, Autocomplete, Nachricht bearbeitet, eigener Text der neuen Sprache wird verwendet.
- [ ] **15. `setmessage` (A9)**: Modal (Absatzfeld, vorbefüllt, max. 1800 Zeichen damit Platz für 25 Rollen bleibt), speichern pro Sprache,
  leer → Standard; aktives Panel aktualisieren.
  *Abnahme:* Tests: Modal-Vorbelegung, speichern, zurücksetzen, Panel-Update, Länge.
- [ ] **16. `sethierarchie` (A3)**: Parameter `ebene` (1–100), speichern, im Manager setzen, Willkommenskanal neu anordnen.
  *Abnahme:* Tests: Wert gespeichert, Bereichsgrenzen, `arrange` aufgerufen.
- [ ] **17. Robustheit + Integration (A12/A4)**: Listener `on_guild_role_delete`, `on_guild_channel_delete`; Integrationstest
  start → Klick → Rolle → Sprache wechseln → stop; neues Cog mit gleichen Dateien kennt den Zustand.
  *Abnahme:* Tests grün.
- [ ] **18. Doku**: README (Modul `rolepanel`, Befehle, Bot-Recht „Rollen verwalten“, Bot-Rolle über den wählbaren Rollen,
  Willkommenskanal/Hierarchie für künftige Module); TESTS_FUER_DICH vollständig (T1…).
  *Abnahme:* README aktualisiert, Tests T1… nummeriert mit Einspiel-Anleitung.
- [ ] **19. (manuell)** Tests aus `docs/TESTS_FUER_DICH.md` in Discord durchführen, Ergebnis in `docs/FEEDBACK.md`.
  *Abnahme:* alle Abnahmekriterien des Lastenhefts mit OK bestätigt.
