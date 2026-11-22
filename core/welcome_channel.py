from __future__ import annotations

import copy
import json
import logging
import inspect
import os
from pathlib import Path
from typing import Any, Callable

import discord

logger = logging.getLogger("discordbot.welcome")

# Projektwurzel: core/welcome_channel.py -> eine Ebene höher.
DEFAULT_PATH = Path(__file__).resolve().parents[1] / "data" / "welcome_channel.json"

DEFAULT_SETTINGS: dict[str, Any] = {
    "channel_id": None,
    # Pro Anbieter-Schlüssel: {"message_id": int | None, "hierarchy": int}
    "posts": {},
}


class WelcomeChannelStorage:
    """Speichert den gemeinsamen Willkommenskanal pro Guild als JSON-Datei."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = Path(path) if path is not None else DEFAULT_PATH

    def _read_all(self) -> dict[str, Any]:
        try:
            with self.path.open("r", encoding="utf-8") as file:
                data = json.load(file)
        except FileNotFoundError:
            return {}
        except (OSError, json.JSONDecodeError):
            logger.exception("%s ist nicht lesbar; es werden Standardwerte verwendet.", self.path)
            return {}
        if not isinstance(data, dict):
            logger.error("%s enthält kein JSON-Objekt; es werden Standardwerte verwendet.", self.path)
            return {}
        return data

    def _write_all(self, data: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = self.path.with_name(f".{self.path.name}.tmp")
        with temporary_path.open("w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
            file.write("\n")
            file.flush()
            os.fsync(file.fileno())
        os.replace(temporary_path, self.path)

    def load(self, guild_id: int) -> dict[str, Any]:
        """Liefert die Einstellungen der Guild; fehlende Werte werden mit Standardwerten ergänzt."""
        settings = copy.deepcopy(DEFAULT_SETTINGS)
        stored = self._read_all().get(str(guild_id))
        if isinstance(stored, dict):
            for key in DEFAULT_SETTINGS:
                if key in stored:
                    settings[key] = stored[key]
        if not isinstance(settings["posts"], dict):
            settings["posts"] = {}
        return settings

    def save(self, guild_id: int, settings: dict[str, Any]) -> None:
        """Speichert die Einstellungen der Guild; andere Guilds bleiben unverändert."""
        data = self._read_all()
        data[str(guild_id)] = {
            key: settings.get(key, copy.deepcopy(DEFAULT_SETTINGS[key])) for key in DEFAULT_SETTINGS
        }
        self._write_all(data)

    def update(self, guild_id: int, **changes: Any) -> dict[str, Any]:
        """Ändert einzelne Werte, speichert und gibt die neuen Einstellungen zurück."""
        unknown = set(changes) - set(DEFAULT_SETTINGS)
        if unknown:
            raise KeyError(f"Unbekannte Einstellung(en): {', '.join(sorted(unknown))}")
        settings = self.load(guild_id)
        settings.update(changes)
        self.save(guild_id, settings)
        return settings


WELCOME_CHANNEL_NAME = "willkommen"


class WelcomeChannelManager:
    """Verwaltet den gemeinsamen Willkommenskanal (ein Kanal pro Guild für alle Module)."""

    def __init__(self, bot: Any, storage: WelcomeChannelStorage | None = None) -> None:
        self.bot = bot
        self.storage = storage if storage is not None else WelcomeChannelStorage()
        # Anbieter-Schlüssel -> render(guild) -> (Text, View | None); darf auch async sein.
        self.providers: dict[str, Callable[[discord.Guild], Any]] = {}

    # --- Anbieter -----------------------------------------------------------------------

    def register(self, key: str, render: Callable[[discord.Guild], Any]) -> None:
        """Meldet einen Anbieter an (erneutes Anmelden ersetzt die Render-Funktion, z. B. nach Reload)."""
        self.providers[key] = render

    def unregister(self, key: str) -> None:
        """Meldet einen Anbieter ab; seine Nachricht bleibt im Kanal stehen."""
        self.providers.pop(key, None)

    async def _render(self, guild: discord.Guild, key: str) -> tuple[str, discord.ui.View | None]:
        result = self.providers[key](guild)
        if inspect.isawaitable(result):
            result = await result
        content, view = result
        return content, view

    @staticmethod
    def _mentions(ping: bool) -> discord.AllowedMentions:
        # Rollen-/Nutzererwähnungen im Text pingen nie; @everyone nur beim ersten Posten.
        return discord.AllowedMentions(everyone=ping, roles=False, users=False, replied_user=False)

    async def _send(
        self, guild: discord.Guild, channel: discord.TextChannel, key: str, ping: bool
    ) -> int | None:
        """Sendet die Nachricht des Anbieters neu; liefert die Message-ID oder None bei Fehler."""
        try:
            content, view = await self._render(guild, key)
            kwargs: dict[str, Any] = {"content": content, "allowed_mentions": self._mentions(ping)}
            if view is not None:
                kwargs["view"] = view
            message = await channel.send(**kwargs)
        except discord.HTTPException:
            logger.exception("Nachricht von '%s' konnte nicht gesendet werden (Guild %s).", key, guild.id)
            return None
        return message.id

    async def _delete(self, channel: discord.TextChannel, message_id: int) -> None:
        try:
            await channel.get_partial_message(message_id).delete()
        except discord.NotFound:
            pass
        except discord.HTTPException:
            logger.exception("Nachricht %s konnte nicht gelöscht werden.", message_id)

    def _set_post(self, guild_id: int, key: str, **changes: Any) -> None:
        settings = self.storage.load(guild_id)
        post = settings["posts"].get(key)
        post = dict(post) if isinstance(post, dict) else {"message_id": None, "hierarchy": 10}
        post.update(changes)
        settings["posts"][key] = post
        self.storage.save(guild_id, settings)

    # --- Posten + Anordnen -----------------------------------------------------------------

    async def publish(
        self, guild: discord.Guild, key: str, hierarchy: int, ping: bool = False
    ) -> int | None:
        """Postet bzw. aktualisiert die Nachricht des Anbieters und ordnet den Kanal."""
        channel = await self.ensure_channel(guild)
        self._set_post(guild.id, key, hierarchy=hierarchy)
        post = self.storage.load(guild.id)["posts"][key]
        if post.get("message_id") is not None:
            await self.refresh(guild, key)
        else:
            message_id = await self._send(guild, channel, key, ping)
            self._set_post(guild.id, key, message_id=message_id)
            await self.arrange(guild)
        return self.storage.load(guild.id)["posts"][key].get("message_id")

    async def refresh(self, guild: discord.Guild, key: str) -> None:
        """Bearbeitet die gepostete Nachricht; fehlt sie, wird sie ohne Ping neu gesendet."""
        channel = self.get_channel(guild)
        post = self.storage.load(guild.id)["posts"].get(key)
        if channel is None or not isinstance(post, dict) or post.get("message_id") is None:
            return
        try:
            content, view = await self._render(guild, key)
            await channel.get_partial_message(post["message_id"]).edit(
                content=content, view=view, allowed_mentions=self._mentions(False)
            )
        except discord.NotFound:
            message_id = await self._send(guild, channel, key, False)
            self._set_post(guild.id, key, message_id=message_id)
            await self.arrange(guild)
        except discord.HTTPException:
            logger.exception("Nachricht von '%s' konnte nicht bearbeitet werden (Guild %s).", key, guild.id)

    async def remove(self, guild: discord.Guild, key: str) -> None:
        """Löscht die Nachricht des Anbieters und vergisst den Eintrag."""
        settings = self.storage.load(guild.id)
        post = settings["posts"].pop(key, None)
        self.storage.save(guild.id, settings)
        channel = self.get_channel(guild)
        if channel is not None and isinstance(post, dict) and post.get("message_id") is not None:
            await self._delete(channel, post["message_id"])

    async def set_hierarchy(self, guild: discord.Guild, key: str, hierarchy: int) -> None:
        """Setzt die Hierarchieebene und ordnet den Kanal neu."""
        self._set_post(guild.id, key, hierarchy=hierarchy)
        await self.arrange(guild)

    def _posted(self, guild_id: int) -> list[tuple[str, dict[str, Any]]]:
        """Gepostete Nachrichten registrierter Anbieter in Soll-Reihenfolge (Ebene, Schlüssel)."""
        posts = self.storage.load(guild_id)["posts"]
        items = [
            (key, post)
            for key, post in posts.items()
            if isinstance(post, dict) and post.get("message_id") is not None and key in self.providers
        ]
        items.sort(key=lambda item: (item[1].get("hierarchy", 10), item[0]))
        return items

    async def arrange(self, guild: discord.Guild) -> None:
        """Ordnet die Bot-Nachrichten: ab der ersten Abweichung löschen und in Soll-Reihenfolge neu senden."""
        channel = self.get_channel(guild)
        if channel is None:
            return
        desired = self._posted(guild.id)
        actual = sorted(desired, key=lambda item: item[1]["message_id"])
        start = next((i for i, (d, a) in enumerate(zip(desired, actual)) if d[0] != a[0]), None)
        if start is None:
            return
        for key, post in desired[start:]:
            await self._delete(channel, post["message_id"])
            message_id = await self._send(guild, channel, key, False)
            self._set_post(guild.id, key, message_id=message_id)

    async def move_channel(self, guild: discord.Guild, channel: discord.TextChannel) -> None:
        """Wechselt den Kanal: alte Nachrichten löschen, im neuen geordnet ohne Ping neu senden."""
        old = self.get_channel(guild)
        settings = self.storage.load(guild.id)
        if old is not None:
            for post in settings["posts"].values():
                if isinstance(post, dict) and post.get("message_id") is not None:
                    await self._delete(old, post["message_id"])
        to_resend = [key for key, _ in self._posted(guild.id)]
        for post in settings["posts"].values():
            if isinstance(post, dict):
                post["message_id"] = None
        settings["channel_id"] = channel.id
        self.storage.save(guild.id, settings)
        for key in to_resend:
            message_id = await self._send(guild, channel, key, False)
            self._set_post(guild.id, key, message_id=message_id)

    def get_channel(self, guild: discord.Guild) -> discord.TextChannel | None:
        """Gibt den gesetzten Kanal zurück oder None (nicht gesetzt bzw. nicht mehr vorhanden)."""
        channel_id = self.storage.load(guild.id)["channel_id"]
        if channel_id is None:
            return None
        channel = guild.get_channel(channel_id)
        return channel if isinstance(channel, discord.TextChannel) else None

    def set_channel(self, guild: discord.Guild, channel: discord.TextChannel) -> None:
        """Setzt den Willkommenskanal (überschreibt einen vorhandenen)."""
        self.storage.update(guild.id, channel_id=channel.id)

    async def ensure_channel(self, guild: discord.Guild) -> discord.TextChannel:
        """Liefert den Kanal; sonst vorhandenen „willkommen“ nutzen oder neu anlegen (Forbidden wird weitergereicht)."""
        channel = self.get_channel(guild)
        if channel is None:
            channel = discord.utils.find(
                lambda c: c.name.lower() == WELCOME_CHANNEL_NAME, guild.text_channels
            )
            if channel is None:
                channel = await guild.create_text_channel(WELCOME_CHANNEL_NAME)
                logger.info("Willkommenskanal #%s auf Guild %s angelegt.", channel.name, guild.id)
            self.set_channel(guild, channel)
        return channel

    def handle_channel_deleted(self, guild_id: int, channel_id: int) -> bool:
        """Setzt Kanal und Post-IDs zurück, wenn der gelöschte Kanal der Willkommenskanal war."""
        settings = self.storage.load(guild_id)
        if settings["channel_id"] != channel_id:
            return False
        posts = {}
        for key, post in settings["posts"].items():
            if isinstance(post, dict):
                posts[key] = dict(post, message_id=None)
        self.storage.update(guild_id, channel_id=None, posts=posts)
        return True


def get_welcome_manager(bot: Any) -> WelcomeChannelManager:
    """Gibt die Manager-Instanz am Bot zurück (wird einmal angelegt, überlebt Modul-Reloads)."""
    manager = getattr(bot, "welcome_manager", None)
    if not isinstance(manager, WelcomeChannelManager):
        manager = WelcomeChannelManager(bot)
        bot.welcome_manager = manager
    return manager
