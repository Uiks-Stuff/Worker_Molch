# Feedback zu den Tests

Format: Testnummer – OK / FEHLER – was ist passiert (Fehlermeldung, Screenshot-Beschreibung, Log-Auszug)

T1 – Pong! Latenz: 140 ms; 
T1 - Ausführung /module list -> Verfügbare Bot-Module: clear — :green_circle: aktiv, honeypot — :white_circle: deaktiviert

T2 – Modul geladen
T2 - 1. 7 Unterbefehle gefunden
T2 - 2. Überwachung: inaktiv, Channel: nicht gesetzt, Save-Roles: keine, Sprache: DEUTSCH, Gebannte User: 0
T2 - Zusatz: Commands nicht verfügbar ohne Rechte

T3 - 1. passt
T3 - 2. passt
T3 - 3. passt
T3 - 4. passt
T3 - 5. passt
T3 - 6. passt
T3 - Zusatz: passt nur für mich sichtbar

T4 - 1. passt, überwachung standardmäßig inaktiv
T4 - 2. passt
T4 - 3. passt
T4 - 4. passt

T5 - 1. passt Channel erstellt, Mitglieder gepingt, NAchricht geschrieben
T5 - 2. passt
T5 - 3. passt, NAchricht bearbeitet
T5 - 4. passt
T5 - 5. passt
T5 - 6. passt, funktioniert
T5 - 7. kann nicht getestet werden, Manage Message betrifft nur Nachrichten anderer User
T5 - Optional entfällt

T6 - 1. passt
T6 - 2. passt
T6 - 3. passt
T6 - 4. passt
T6 - 5. passt

T7 - 1. passt
T7 - 2. passt
T7 - 3. passt, nur mit richtiger rolle kann ich diese lesen
T7 - 4. passt, kein Ban
T7 - 5. passt, kein Ban
T7 - 6. Ban schlägt nicht fehl, wird gebannt, ist nicht weiter schlimm
T7 - 7. passt
T7 - 8. passt
T7 - Optinal: passt

T8 - 1. lange offline nach restart -> Log:
discord-bot  | 2026-11-18 21:02:14,565 | WARNING | discord.client | PyNaCl is not installed, voice will NOT be supported
discord-bot  | 2026-11-18 21:02:14,565 | WARNING | discord.client | davey is not installed, voice will NOT be supported
discord-bot  | 2026-11-18 21:02:14,566 | INFO | discord.client | logging in using static token
discord-bot  | 2026-11-18 21:02:15,189 | INFO | discordbot.modules | Modul geladen: modules.clear.cog
discord-bot  | 2026-11-18 21:02:15,200 | INFO | discordbot.modules | Modul geladen: modules.honeypot.cog
discord-bot  | 2026-11-18 21:02:15,467 | INFO | discordbot | 4 Slash-Command(s) für Server 861256373152907265 synchronisiert.
discord-bot  | 2026-11-18 21:03:18,101 | INFO | discord.gateway | Shard ID None session has been invalidated.
discord-bot  | 2026-11-18 21:02:14,565 | WARNING | discord.client | PyNaCl is not installed, voice will NOT be supported
discord-bot  | 2026-11-18 21:02:14,565 | WARNING | discord.client | davey is not installed, voice will NOT be supported
discord-bot  | 2026-11-18 21:02:14,566 | INFO | discord.client | logging in using static token
discord-bot  | 2026-11-18 21:02:15,189 | INFO | discordbot.modules | Modul geladen: modules.clear.cog
discord-bot  | 2026-11-18 21:02:15,200 | INFO | discordbot.modules | Modul geladen: modules.honeypot.cog
discord-bot  | 2026-11-18 21:02:15,467 | INFO | discordbot | 4 Slash-Command(s) für Server 861256373152907265 synchronisiert.
discord-bot  | 2026-11-18 21:03:18,101 | INFO | discord.gateway | Shard ID None session has been invalidated.
discord-bot  | 2026-11-18 21:05:15,461 | INFO | discord.gateway | Shard ID None session has been invalidated.
discord-bot  | 2026-11-18 21:05:21,447 | INFO | discord.gateway | Shard ID None has connected to Gateway (Session ID: a58ad4e9acbd709cc02873bf236dcd8b).
discord-bot  | 2026-11-18 21:05:23,453 | INFO | discordbot | Bot angemeldet als Worker Molch#6847 (ID: 1571516795154862180)

T8 - 2. passt
T8 - 3. passt
T8 - 4. passt
T8 - 5. alle funktionen wie gefordert
[erledigt] T1–T8 vollständig ausgewertet, keine Fehler.
