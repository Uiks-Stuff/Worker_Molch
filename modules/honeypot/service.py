from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from datetime import datetime

import discord
from discord.ext import commands

from .languages import LanguageError, render_info, resolve_language
from .storage import HoneypotStorage

logger = logging.getLogger("discordbot.honeypot")

HISTORY_LIMIT = 50
BAN_REASON = "Honeypot: Nachricht im überwachten Channel"
# Entfernt bei einem Bann die Nachrichten des Users der letzten Stunde (serverweit).
DELETE_MESSAGE_SECONDS = 3600
# So lange wird ein User nach einem Bann(versuch) nicht erneut behandelt (Nachrichten, die schon unterwegs sind).
RECENT_SECONDS = 60


@dataclass
class MessageSnapshot:
    """Vor dem Bann lokal gesicherte Nachrichtendaten (fürs Log)."""

    user_id: int
    user_name: str
    content: str
    attachment_count: int
    created_at: datetime


class HoneypotService:
    """Fachlogik des Honeypot-Moduls (ohne Slash-Command-Schicht)."""

    def __init__(self, bot: commands.Bot, storage: HoneypotStorage) -> None:
        self.bot = bot
        self.storage = storage
        # (guild_id, user_id) -> Zeitpunkt (monotonic); verhindert Doppelbanns und doppelte Zählung.
        self._handled: dict[tuple[int, int], float] = {}

    # ------------------------------------------------------------------- Bann
    @staticmethod
    def _is_exempt(message: discord.Message, settings: dict) -> bool:
        """Bot, Webhook, Systemnachricht, Servereigentümer, Moderator/Admin oder Save-Role."""
        author = message.author
        if getattr(author, "bot", False) or message.webhook_id is not None or message.is_system():
            return True
        if author.id == message.guild.owner_id:
            return True
        permissions = getattr(author, "guild_permissions", None)
        if permissions is not None and (permissions.ban_members or permissions.administrator):
            return True
        safe = set(settings["safe_role_ids"])
        return any(role.id in safe for role in getattr(author, "roles", []))

    def _already_handled(self, key: tuple[int, int]) -> bool:
        now = time.monotonic()
        for old_key in [k for k, t in self._handled.items() if now - t > RECENT_SECONDS]:
            del self._handled[old_key]
        return key in self._handled

    async def handle_message(self, message: discord.Message) -> bool:
        """Bannt den Absender, wenn die Nachricht im überwachten Channel liegt. True = Bann erfolgt."""
        guild = message.guild
        if guild is None:
            return False
        settings = self.storage.load(guild.id)
        if not settings["active"] or message.channel.id != settings["channel_id"]:
            return False
        if self._is_exempt(message, settings):
            return False

        author = message.author
        key = (guild.id, author.id)
        if self._already_handled(key):
            return False
        # Sofort markieren (vor dem ersten await), damit parallele Nachrichten übersprungen werden.
        self._handled[key] = time.monotonic()

        snapshot = MessageSnapshot(
            user_id=author.id,
            user_name=str(author),
            content=message.content or "",
            attachment_count=len(message.attachments),
            created_at=message.created_at,
        )

        # Bann hat Vorrang: erster API-Aufruf.
        try:
            await guild.ban(author, reason=BAN_REASON, delete_message_seconds=DELETE_MESSAGE_SECONDS)
        except discord.HTTPException as exc:  # inkl. Forbidden
            logger.warning("Bann von %s in Guild %s fehlgeschlagen: %s", author.id, guild.id, exc)
            await self._log_event(guild, snapshot, banned=False, error=str(exc))
            return False

        try:
            await message.delete()
        except discord.NotFound:
            pass  # durch delete_message_seconds ggf. schon entfernt
        except discord.HTTPException:
            logger.warning("Honeypot-Nachricht %s konnte nicht gelöscht werden.", message.id)

        await self._log_event(guild, snapshot, banned=True)
        await self._record_ban(guild)
        return True

    async def _log_event(
        self, guild: discord.Guild, snapshot: MessageSnapshot, banned: bool, error: str | None = None
    ) -> None:
        """Ereignislog im Thread (Aufgabe 12)."""

    async def _record_ban(self, guild: discord.Guild) -> None:
        """Zähler erhöhen und Infonachricht aktualisieren (Aufgabe 11)."""

    async def handle_channel_deleted(self, channel: discord.abc.GuildChannel) -> bool:
        """Überwachter Channel gelöscht -> Überwachung aus, Verweise zurücksetzen."""
        settings = self.storage.load(channel.guild.id)
        if settings["channel_id"] != channel.id:
            return False
        self.storage.update(
            channel.guild.id, active=False, channel_id=None, info_message_id=None, log_thread_id=None
        )
        logger.info("Honeypot-Channel %s in Guild %s gelöscht; Überwachung beendet.", channel.id, channel.guild.id)
        return True

    # ------------------------------------------------------------ Infonachricht
    async def _find_info_message(
        self, channel: discord.TextChannel, settings: dict
    ) -> tuple[discord.Message | None, bool]:
        """Sucht die Infonachricht. Rückgabe: (Nachricht, gespeicherte ID war ungültig)."""
        message_id = settings["info_message_id"]
        if message_id:
            try:
                return await channel.fetch_message(message_id), False
            except discord.NotFound:
                return None, True

        # Keine ID gespeichert (z. B. Datei verloren): eigene Nachricht im Verlauf übernehmen.
        bot_user = self.bot.user
        if bot_user is not None:
            async for message in channel.history(limit=HISTORY_LIMIT):
                if message.author.id == bot_user.id:
                    return message, False
        return None, False

    async def delete_info_message(self, guild: discord.Guild) -> None:
        """Löscht die gespeicherte Infonachricht (Fehler werden geloggt) und vergisst ihre ID."""
        settings = self.storage.load(guild.id)
        channel_id, message_id = settings["channel_id"], settings["info_message_id"]
        channel = guild.get_channel(channel_id) if channel_id else None
        if channel is not None and message_id:
            try:
                message = await channel.fetch_message(message_id)
                await message.delete()
            except discord.NotFound:
                pass
            except discord.HTTPException:
                logger.exception("Alte Infonachricht in Guild %s konnte nicht gelöscht werden.", guild.id)
        if message_id:
            self.storage.update(guild.id, info_message_id=None)

    async def update_info_message(self, guild: discord.Guild, setup: bool = False) -> discord.Message | None:
        """Sendet bzw. bearbeitet die Infonachricht im überwachten Channel.

        Nur bei `setup=True` und wenn noch keine Nachricht existiert, wird `@everyone`
        gepingt. Fehler werden geloggt und nicht weitergereicht.
        """
        settings = self.storage.load(guild.id)
        channel_id = settings["channel_id"]
        channel = guild.get_channel(channel_id) if channel_id else None
        if channel is None:
            return None

        try:
            _, lines = resolve_language(settings["language"])
        except LanguageError:
            logger.exception("Keine nutzbare Sprache für Guild %s.", guild.id)
            return None
        text = render_info(lines, settings["ban_count"], settings["active"])

        try:
            message, id_invalid = await self._find_info_message(channel, settings)
            if message is not None:
                if message.content != text:
                    await message.edit(content=text, allowed_mentions=discord.AllowedMentions.none())
                if message.id != settings["info_message_id"]:
                    self.storage.update(guild.id, info_message_id=message.id)
                return message

            # Neu senden: Ping nur beim erstmaligen Aufsetzen, nie nach gelöschter Nachricht.
            ping = setup and not id_invalid
            mentions = discord.AllowedMentions(everyone=True) if ping else discord.AllowedMentions.none()
            message = await channel.send(text, allowed_mentions=mentions)
            self.storage.update(guild.id, info_message_id=message.id)
            return message
        except discord.HTTPException:
            logger.exception("Infonachricht in Guild %s konnte nicht aktualisiert werden.", guild.id)
            return None
