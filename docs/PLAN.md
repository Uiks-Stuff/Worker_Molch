# Plan: Modul `honeypot` (Honeypot Moderator)

Quelle: `docs/LASTENHEFT.md`. Tests: `.venv/bin/pytest -q` (`tests/`, Mocks mit `spec=discord.…`, keine Discord-Verbindung).

## Architektur
- `core/` nur minimal (Aufgabe 1: Intents + Fehlertext). Alles andere in `modules/honeypot/`:
  - `storage.py` – Guild-Einstellungen als JSON in `data/honeypot.json` (atomar schreiben wie `ModuleManager`).
    Pfad relativ zur Projektwurzel; `data/` ist im Container beschreibbar, `modules/` nur lesbar (`:ro`).
  - `languages.py` + `languages.txt` – Sprachdatei, bei jedem Zugriff neu gelesen (Erweitern ohne Reload).
  - `service.py` – Fachlogik ohne Slash-Command-Schicht (Bann-Entscheidung, Infonachricht, Log-Thread, Zähler).
  - `cog.py` – `GroupCog` `/honeypot` + Listener (`on_message`, `on_guild_channel_delete`), `async def setup(bot)`.
- Gespeichert pro Guild: `active`, `channel_id`, `safe_role_ids`, `language`, `ban_count`, `info_message_id`, `log_thread_id`.

## Anforderungen
- A0: Gateway-Intents `guild_messages` (für `on_message`) und `message_content` (privilegiert, für „Nachricht“ im Log).
- A1: Persistenz von Status, Channel, Save-Roles, Sprache, Ban-Zähler; Zustand überlebt Neustart und `/module reload`.
- A2: Sprachdatei im Format `[NAME]` + Zeilen ` - …`; Platzhalter `X` = Ban-Anzahl; beliebig erweiterbar.
  Zeilen positionsbezogen: 1 = Infotext, 2 = Ban-Zeile, 3 (optional) = Zusatz bei inaktiver Überwachung
  (Standard: „Honeypot under construction“).
- A3: `/honeypot start|stop|status|channel|setrole|removerole|setlanguage` – nur Moderatoren/Admins, nur auf Servern, Antworten ephemeral.
  Discord erlaubt nur kleingeschriebene Befehlsnamen → `setRole` → `setrole` usw.
- A4 (F1): Nachricht im überwachten Channel bei aktiver Überwachung → Bann, außer Save-Role, Moderator/Admin, Bot, Webhook, Servereigentümer.
- A5 (F2): Ereignislog in privatem Thread des Channels: User-ID, Name, Banngrund, Nachricht (+ Hinweis auf Anhänge), Zeitpunkt;
  auch fehlgeschlagene Banns (z. B. Rollenhierarchie) werden geloggt.
- A6 (F3): Infonachricht im Channel (Text + Ban-Anzahl), wird bei Ban, Sprach- und Channelwechsel, start und stop aktualisiert bzw. neu erstellt.
  Bei inaktiver Überwachung bekommt sie den Zusatz aus Zeile 3 der Sprachdatei.
  `@everyone` pingt nur einmal beim Aufsetzen des Channels – nicht nach Neustart, nicht beim Bearbeiten, nicht wenn die Nachricht schon existiert.
- A7: Robustheit: jeder User wird nur einmal gebannt/gezählt (mehrere Nachrichten gleichzeitig), gelöschter Channel → Überwachung aus,
  gelöschte Info-Nachricht/Thread → neu erstellen, archivierter Thread wird weiterverwendet, fehlende Bot-Rechte → verständliche Meldung.

## Aufgaben
- [x] **1. Core-Intents (A0)**: `main.py`: `intents.guild_messages = True`, `intents.message_content = True`; Label `ban_members` im Error-Handler.
  *Abnahme:* Test prüft Intents + Label; alle Tests grün; T1 in TESTS_FUER_DICH (erst Intent im Developer Portal aktivieren,
  dann Rebuild – sonst startet der Bot wegen `PrivilegedIntentsRequired` gar nicht).
- [x] **2. Speicher (A1)**: `modules/honeypot/__init__.py`, `storage.py` (Defaults, laden/speichern pro Guild, atomar).
  *Abnahme:* Tests: Defaults bei fehlender/defekter Datei, Roundtrip, Guilds getrennt, `data/` wird angelegt.
- [x] **3. Sprachdatei (A2)**: `languages.txt` mit `[DEUTSCH]` (Text aus Lastenheft + Zeile 3 „Honeypot under construction“) und `[ENGLISH]`;
  Parser: Namen case-insensitive, führende Leerzeichen/`- ` entfernen, `X` (als eigenes Wort) → Zahl, fehlende Zeile 3 → Standardtext,
  unbekannte Sprache → Fehler, gespeicherte aber entfernte Sprache → Fallback DEUTSCH. Text aktiv/inaktiv rendern.
  *Abnahme:* Tests für alle genannten Fälle inkl. leerer Abschnitt und fehlender Zeile 3.
- [ ] **4. Gerüst + `/honeypot status` (A3)**: `cog.py` mit `GroupCog` (`guild_only`, `default_permissions` + `checks.has_permissions(ban_members=True)`), `setup(bot)`;
  status: aktiv/inaktiv, Channel, Save-Roles (gelöschte Rollen ausblenden), Sprache, Ban-Anzahl.
  *Abnahme:* Test: alle 7 Befehlsnamen registriert & kleingeschrieben, Rechte-Dekoratoren gesetzt, status-Text per Mock-Interaction. Smoke-Test lädt Extension.
- [ ] **5. `/honeypot setrole` / `removerole` (A3)**: `rolle1` Pflicht, `rolle2`–`rolle5` optional; `@everyone` und Bot-verwaltete Rollen ablehnen; Duplikate/nicht gesetzte Rollen melden.
  *Abnahme:* Tests hinzufügen, entfernen, Duplikate, Ablehnungen.
- [ ] **6. Infonachricht (A6)** in `service.py`: `update_info_message(guild, setup=False)` sendet/bearbeitet (Text je nach aktiv/inaktiv);
  vorhandene Nachricht finden: gespeicherte ID, sonst eigene Bot-Nachricht in den letzten 50 Nachrichten übernehmen;
  nur wenn `setup=True` und keine Nachricht existiert → mit `@everyone`-Ping senden (`AllowedMentions(everyone=True)` explizit,
  da Bot global `none()` nutzt); sonst ohne Ping. Bei `NotFound` ohne Ping neu senden + ID speichern.
  *Abnahme:* Tests: Setup-Ping, kein Ping bei Neustart/Bearbeiten/vorhandener Nachricht, vorhandene Bot-Nachricht übernommen,
  NotFound → neu ohne Ping, Zusatz bei inaktiv, kein Channel → nichts.
- [ ] **7. `/honeypot channel` (A3/A6)**: optionaler Parameter `channel` (TextChannel). Setzen/Wechsel: alte Infonachricht löschen, Thread-ID zurücksetzen,
  bei aktiver Überwachung Infonachricht im neuen Channel. Ohne Parameter: Channel entfernen + Überwachung stoppen.
  *Abnahme:* Tests setzen, wechseln, entfernen.
- [ ] **8. `/honeypot start` / `stop` (A3)**: start ohne gesetzten Channel: vorhandenen Textchannel „honeypot“ (Name case-insensitive) verwenden,
  sonst anlegen, und setzen. Bot-Rechte im Channel prüfen (Kanal ansehen, Nachrichten senden, Verlauf lesen, Nachrichten verwalten,
  Mitglieder bannen, @everyone erwähnen, private Threads erstellen, in Threads senden) → fehlende verständlich melden;
  aktivieren + Infonachricht (`setup=True`). stop: deaktivieren, Infonachricht mit Zusatz „under construction“ bearbeiten.
  start nach stop entfernt den Zusatz (ohne Ping). Jeweils „bereits aktiv/inaktiv“ melden.
  *Abnahme:* Tests: Channel gesetzt / vorhandener „honeypot“ / neu angelegt, bereits aktiv/inaktiv, fehlende Rechte,
  `Forbidden` beim Anlegen, stop setzt Zusatz, erneuter start ohne Ping.
- [ ] **9. `/honeypot setlanguage` (A3/A6)**: Parameter `language` mit Autocomplete aus Sprachdatei; speichern; Infonachricht bearbeiten (falls Channel gesetzt).
  *Abnahme:* Tests: gültig (auch Kleinschreibung), ungültig, Autocomplete-Liste, Nachricht bearbeitet.
- [ ] **10. Bann-Logik (A4/A7)**: `on_message`: nur aktiv + `message.channel.id == channel_id` (Nachrichten im Log-Thread zählen nicht);
  Ausnahmen laut A4; Bann sofort als erster API-Aufruf (Nachrichtendaten fürs Log vorher lokal sichern),
  `guild.ban(author, reason=…, delete_message_seconds=3600)`, danach Honeypot-Nachricht sofort löschen (`NotFound` ignorieren);
  Log/Zähler/Info erst danach. Pro Guild Set „in Bearbeitung“ gegen Doppelbann;
  `Forbidden/HTTPException` abfangen und loggen. `on_guild_channel_delete`: überwachter Channel → Einstellungen zurücksetzen, inaktiv.
  *Abnahme:* Tests: inaktiv, anderer Channel, Thread, Bot, Webhook, Save-Role, Mod, Owner, normaler User, Reihenfolge Bann → Löschen → Log,
  2 Nachrichten gleichzeitig → 1 Ban, Forbidden, Channel gelöscht.
- [ ] **11. Zähler + Info-Update (A1/A6)**: nach erfolgreichem Bann `ban_count += 1`, speichern, Infonachricht aktualisieren.
  *Abnahme:* Test: Zähler nur bei Erfolg, Info-Fehler bricht nicht ab.
- [ ] **12. Log-Thread (A5/A7)**: privater Thread „honeypot-log“ (`invitable=False`) anlegen bzw. per ID holen (`get_thread` → `fetch_channel`, archiviert ok);
  Eintrag als Embed (User-ID, Name, Grund, Nachricht gekürzt auf Limit, Anhänge-Anzahl, Zeit); fehlgeschlagener Bann ebenfalls. Log-Fehler verhindert Bann nicht.
  *Abnahme:* Tests: Thread neu/vorhanden/gelöscht → neu, Inhalt, Kürzung, leerer Inhalt, Log-Fehler.
- [ ] **13. Neustart/Reload + Integration (A1/A7)**: Mock-Ablauf start → Nachricht → Bann → Log → Zähler → Infonachricht; neues Cog mit gleicher Datei kennt Zustand.
  *Abnahme:* Integrationstest grün.
- [ ] **14. Doku**: README: Modul `honeypot` (Befehle, nötige Bot-Rechte, Message Content Intent, Rollenhierarchie: Bot-Rolle über zu bannenden Usern, `data/`-Rechte).
  *Abnahme:* README aktualisiert, TESTS_FUER_DICH vollständig (T1…).
- [ ] **15. (manuell)** Tests aus `docs/TESTS_FUER_DICH.md` in Discord durchführen, Ergebnis in `docs/FEEDBACK.md`.
  *Abnahme:* alle Abnahmekriterien des Lastenhefts mit OK bestätigt.
