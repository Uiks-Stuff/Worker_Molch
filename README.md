# DiscordBot – Starter

Modularer Discord-Bot auf Basis von Python 3.13, discord.py 2.7.1 und Docker Compose.

## Funktionen in dieser ersten Version

- `/ping` – prüft die Verbindung des Bots.
- `/clear` – löscht den gesamten Verlauf des aktuellen Textkanals/Threads.
- `/clear anzahl:50` – löscht die letzten 50 Nachrichten.
- `/clear benutzer:@Mitglied` – löscht alle Nachrichten dieses Mitglieds.
- `/clear anzahl:50 benutzer:@Mitglied` – löscht die letzten 50 Nachrichten dieses Mitglieds.

Jede Löschung erfordert eine explizite Bestätigung. Die Befehle stehen nur Mitgliedern mit `Nachrichten verwalten` zur Verfügung. Der Bot braucht im jeweiligen Kanal `Kanal ansehen`, `Nachrichtenverlauf anzeigen` und `Nachrichten verwalten`.

## Installation

1. `.env.example` nach `.env` kopieren.
2. `DISCORD_TOKEN` und `GUILD_ID` in `.env` eintragen.
3. Die Verzeichnisse `data` und `logs` auf dem Host für UID/GID 10001 schreibbar machen:

   ```bash
   sudo chown -R 10001:10001 data logs
   ```

4. Container bauen und starten:

   ```bash
   docker compose up -d --build
   ```

5. Logs ansehen:

   ```bash
   docker compose logs -f
   ```

## Module aktivieren/deaktivieren

In `config/modules.json` stehen die beim Start geladenen Extensions. Ein Modul wird aktiviert, indem sein Python-Modulname in `enabled_modules` aufgenommen wird. Zum Deaktivieren den Eintrag entfernen und den Container neu starten:

```bash
docker compose restart
```

Die Verwaltung der Module direkt über Slash-Commands ist für einen späteren Ausbauschritt vorgesehen.

## Discord Developer Portal

OAuth2-Scopes beim Einladen: `bot` und `applications.commands`.

Bot-Berechtigungen: `View Channels`, `Read Message History` und `Manage Messages`.

Für diese Slash-Commands ist kein Message Content Intent erforderlich.

## Hinweise zur Nachrichtenlöschung

Discord erlaubt das Bulk-Löschen nur für Nachrichten, die nicht älter als 14 Tage sind. Ältere Nachrichten werden einzeln gelöscht. Das kann bei großen Verläufen deutlich länger dauern. Discord.py übernimmt das Rate-Limit-Handling.

`/clear anzahl:X benutzer:@Mitglied` durchsucht den Verlauf von den neuesten Nachrichten rückwärts und zählt nur Nachrichten dieses Mitglieds, bis X passende Nachrichten gefunden wurden.

Die Löschung ist endgültig und kann nicht rückgängig gemacht werden.
