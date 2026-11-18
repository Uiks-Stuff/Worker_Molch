# Plan: Modul `honeypot` (Honeypot Moderator)

Quelle: `docs/LASTENHEFT.md`. Neues Modul `modules/honeypot/{__init__.py,cog.py,...}`; `core/` nur minimal (A0).
Tests: `.venv/bin/pytest -q` (Verzeichnis `tests/`, Mocks, keine Discord-Verbindung).

## Anforderungen
- A0: Bot braucht Gateway-Intents für Nachrichten (`guild_messages`, `message_content`) und Fehlertext für `ban_members` (Core, Rebuild nötig).
- A1: Persistenz pro Server (JSON in `data/honeypot.json`): aktiv/inaktiv, Channel, Save-Roles, Sprache, Ban-Zähler, Thread-ID, Info-Nachricht-ID.
- A2: Sprachdatei `modules/honeypot/languages.txt` im Format `[DEUTSCH]` + Listenzeilen `- …` (Infotext, `Bans: X`); beliebig erweiterbar.
- A3: Slash-Gruppe `/honeypot` mit start, stop, status, channel, setRole, removeRole, setLanguage; nur Moderatoren/Admins.
- A4: F1 – Nachricht im überwachten Channel (solange aktiv) → Autor wird gebannt, außer Save-Role/Bot/Mod.
- A5: F2 – Ereignislog in privatem Thread des Channels (nur Mods/Admins sichtbar): User-ID, Banngrund, Nachricht.
- A6: F3 – Infonachricht im Channel mit Ban-Anzahl, passt sich bei Ban und Sprachwechsel an.

## Annahmen (Details in PROGRESS.md)
- „Moderatoren, Admin“ = Berechtigung **Mitglieder bannen** (`ban_members`) bzw. Administrator.
- Thread = privater Thread; sichtbar für Mitglieder mit „Threads verwalten“/Admin (kein Hinzufügen einzelner Rollen).
- Mods/Admins (ban_members/administrator) und Bots werden nie gebannt.
- `setRole`/`removeRole`: Slash-Commands kennen keine Listen → Parameter `rolle1` (Pflicht) und `rolle2`–`rolle5` (optional).
- Standardsprache: `DEUTSCH`.

## Aufgaben
- [ ] **1. Core anpassen (A0)**: `main.py` Intents `guild_messages` + `message_content`, Label `ban_members` im Error-Handler. *Abnahme:* Test prüft Intents und Fehlertext; bestehende Tests grün. (Rebuild → TESTS_FUER_DICH)
- [ ] **2. Modul-Gerüst + Speicher (A1)**: `modules/honeypot/` mit `setup(bot)`, `storage.py` (atomares JSON, Defaults, pro Guild). *Abnahme:* Tests: Defaults, Schreiben/Lesen, Guilds getrennt, defekte Datei → Defaults.
- [ ] **3. Sprachdatei + Parser (A2)**: `languages.txt` mit `[DEUTSCH]` (Text aus Lastenheft) und `[ENGLISH]`; `languages.py` (laden, Namen case-insensitive, `Bans: X` → Zahl einsetzen). *Abnahme:* Tests für Parsing, unbekannte Sprache, Platzhalter.
- [ ] **4. Command-Gruppe + `/honeypot status` (A3)**: Gruppe mit Rechte-Check (`ban_members`, guild_only), status zeigt aktiv/inaktiv, Channel, Save-Roles (+ Sprache, Bans). *Abnahme:* Test mit Mock-Interaction; Rechte-Dekoratoren vorhanden.
- [ ] **5. `/honeypot channel` (A3)**: Parameter optional `channel`; ohne Parameter Channel entfernen (und Überwachung stoppen). *Abnahme:* Tests setzen/ersetzen/entfernen; nur ein Channel.
- [ ] **6. `/honeypot setRole` / `removeRole` (A3)**: `rolle1`–`rolle5`; Duplikate/Nicht-Vorhandenes sinnvoll melden; `@everyone` ablehnen. *Abnahme:* Tests hinzufügen/entfernen/Duplikate.
- [ ] **7. Infonachricht (A6)**: Helfer `update_info_message(guild)`: sendet/bearbeitet Nachricht (Text + `Bans: X` in gewählter Sprache), erstellt sie neu, falls gelöscht. *Abnahme:* Tests: neu erstellt, bearbeitet, bei NotFound neu.
- [ ] **8. `/honeypot start` / `stop` (A3)**: start: aktiviert; ohne gesetzten Channel Textchannel „Honeypot“ anlegen und setzen; Infonachricht posten. stop: deaktiviert. *Abnahme:* Tests: mit/ohne Channel, bereits aktiv, fehlende Bot-Rechte → verständliche Meldung.
- [ ] **9. `/honeypot setLanguage` (A3/A6)**: Parameter `language` (Autocomplete aus Sprachdatei), speichern, Infonachricht aktualisieren. *Abnahme:* Tests: gültig, ungültig, Nachricht wird bearbeitet.
- [ ] **10. Ban-Logik `on_message` (A4)**: nur wenn aktiv + richtiger Channel; ignoriert Bots/Save-Roles/Mods; sonst `guild.ban(...)`; Fehler (Forbidden) abfangen. *Abnahme:* Tests für alle Fälle (inaktiv, anderer Channel, Bot, Save-Role, Mod, normaler User, Forbidden).
- [ ] **11. Ban-Zähler + Info-Update (A1/A6)**: nach erfolgreichem Ban Zähler +1, Infonachricht aktualisieren. *Abnahme:* Test: Zähler steigt nur bei Erfolg.
- [ ] **12. Ereignislog-Thread (A5)**: privater Thread (Name z. B. „Honeypot-Log“) anlegen/wiederfinden, Eintrag mit User-ID, Grund, Nachricht (gekürzt auf Discord-Limit). *Abnahme:* Tests: Thread neu/vorhanden/gelöscht, Inhalt, Kürzung, Log-Fehler verhindert Ban nicht.
- [ ] **13. Integrationstest + Doku**: Ablauf start → Nachricht → Ban → Log → Zähler als Mock-Test; README um Modul `honeypot` ergänzen (Befehle, Bot-Rechte, Intent im Developer Portal). *Abnahme:* alle Tests grün, README aktualisiert.
- [ ] **14. (manuell)** Test in Discord: `docs/TESTS_FUER_DICH.md` (T1…) ausführen, Ergebnis in `FEEDBACK.md`. *Abnahme:* alle Tests OK.
