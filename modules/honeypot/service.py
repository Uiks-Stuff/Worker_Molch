from __future__ import annotations

import logging

import discord
from discord.ext import commands

from .languages import LanguageError, render_info, resolve_language
from .storage import HoneypotStorage

logger = logging.getLogger("discordbot.honeypot")

HISTORY_LIMIT = 50


class HoneypotService:
    """Fachlogik des Honeypot-Moduls (ohne Slash-Command-Schicht)."""

    def __init__(self, bot: commands.Bot, storage: HoneypotStorage) -> None:
        self.bot = bot
        self.storage = storage

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
