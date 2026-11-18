from __future__ import annotations

import logging

import discord
from discord import app_commands
from discord.ext import commands

from .languages import LanguageError, language_names, resolve_language
from .service import HoneypotService
from .storage import HoneypotStorage

logger = logging.getLogger("discordbot.honeypot")

NOT_IMPLEMENTED = "Dieser Befehl ist noch nicht verfügbar."

# Rechte, die der Bot im Honeypot-Channel braucht: (Attribut von discord.Permissions, Anzeigename).
REQUIRED_BOT_PERMISSIONS = [
    ("view_channel", "Kanal ansehen"),
    ("send_messages", "Nachrichten senden"),
    ("read_message_history", "Nachrichtenverlauf anzeigen"),
    ("manage_messages", "Nachrichten verwalten"),
    ("ban_members", "Mitglieder bannen"),
    ("mention_everyone", "@everyone erwähnen"),
    ("create_private_threads", "Private Threads erstellen"),
    ("send_messages_in_threads", "In Threads Nachrichten senden"),
]


@app_commands.guild_only()
@app_commands.default_permissions(ban_members=True)
class Honeypot(commands.GroupCog, name="honeypot", description="Honeypot-Channel zum automatischen Bannen von Scammern."):
    def __init__(self, bot: commands.Bot, storage: HoneypotStorage | None = None) -> None:
        self.bot = bot
        self.storage = storage or HoneypotStorage()
        self.service = HoneypotService(bot, self.storage)
        super().__init__()

    # ------------------------------------------------------------------ status
    @app_commands.command(name="status", description="Zeigt den aktuellen Honeypot-Status.")
    @app_commands.checks.has_permissions(ban_members=True)
    async def status(self, interaction: discord.Interaction) -> None:
        guild = interaction.guild
        settings = self.storage.load(guild.id)

        channel_id = settings["channel_id"]
        channel_text = f"<#{channel_id}>" if channel_id else "nicht gesetzt"

        # Gelöschte Rollen ausblenden.
        roles = [guild.get_role(role_id) for role_id in settings["safe_role_ids"]]
        role_text = ", ".join(role.mention for role in roles if role is not None) or "keine"

        try:
            language, _ = resolve_language(settings["language"])
        except LanguageError:
            language = settings["language"]

        lines = [
            f"**Überwachung:** {'aktiv' if settings['active'] else 'inaktiv'}",
            f"**Channel:** {channel_text}",
            f"**Save-Roles:** {role_text}",
            f"**Sprache:** {language}",
            f"**Gebannte User:** {settings['ban_count']}",
        ]
        await interaction.response.send_message("\n".join(lines), ephemeral=True)

    # ------------------------------------------------- Platzhalter (Aufgaben 5–9)
    @staticmethod
    def _missing_bot_permissions(channel: discord.TextChannel, guild: discord.Guild) -> list[str]:
        """Namen (deutsch) der Rechte, die der Bot im Channel für den Betrieb braucht, aber nicht hat."""
        permissions = channel.permissions_for(guild.me)
        return [label for attribute, label in REQUIRED_BOT_PERMISSIONS if not getattr(permissions, attribute)]

    async def _channel_for_start(self, guild: discord.Guild, settings: dict) -> discord.TextChannel:
        """Gesetzten Channel liefern, sonst vorhandenen „honeypot“ nutzen oder neu anlegen."""
        channel = guild.get_channel(settings["channel_id"]) if settings["channel_id"] else None
        if channel is not None:
            return channel

        channel = next((c for c in guild.text_channels if c.name.lower() == "honeypot"), None)
        if channel is None:
            channel = await guild.create_text_channel("honeypot", reason="Honeypot-Channel")
        # Neuer Channel: alte Verweise (Infonachricht, Log-Thread) sind ungültig.
        self.storage.update(guild.id, channel_id=channel.id, info_message_id=None, log_thread_id=None)
        return channel

    @app_commands.command(name="start", description="Startet die Überwachung.")
    @app_commands.checks.has_permissions(ban_members=True)
    async def start(self, interaction: discord.Interaction) -> None:
        guild = interaction.guild
        settings = self.storage.load(guild.id)
        if settings["active"]:
            await interaction.response.send_message("Die Überwachung ist bereits aktiv.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        try:
            channel = await self._channel_for_start(guild, settings)
        except discord.HTTPException:
            logger.exception("Honeypot-Channel konnte in Guild %s nicht angelegt werden.", guild.id)
            await interaction.followup.send(
                "Ich konnte den Channel „honeypot“ nicht anlegen. Mir fehlt vermutlich das Recht "
                "**Kanäle verwalten** – oder setze mit `/honeypot channel` selbst einen Channel.",
                ephemeral=True,
            )
            return

        missing = self._missing_bot_permissions(channel, guild)
        if missing:
            await interaction.followup.send(
                f"Mir fehlen in {channel.mention} diese Rechte: **{', '.join(missing)}**. "
                "Die Überwachung wurde nicht gestartet.",
                ephemeral=True,
            )
            return

        self.storage.update(guild.id, active=True)
        # setup=True: Ping nur, wenn noch keine Infonachricht existiert (nach stop wird nur bearbeitet).
        message = await self.service.update_info_message(guild, setup=True)
        text = f"Überwachung gestartet in {channel.mention}."
        if message is None:
            text += " Achtung: Die Infonachricht konnte nicht gesendet werden (Details im Bot-Log)."
        await interaction.followup.send(text, ephemeral=True)

    @app_commands.command(name="stop", description="Beendet die Überwachung.")
    @app_commands.checks.has_permissions(ban_members=True)
    async def stop(self, interaction: discord.Interaction) -> None:
        guild = interaction.guild
        if not self.storage.load(guild.id)["active"]:
            await interaction.response.send_message("Die Überwachung ist bereits inaktiv.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        self.storage.update(guild.id, active=False)
        await self.service.update_info_message(guild)
        await interaction.followup.send("Überwachung beendet.", ephemeral=True)

    @app_commands.command(name="channel", description="Setzt den überwachten Channel (ohne Angabe: Channel entfernen).")
    @app_commands.describe(channel="Neuer Honeypot-Channel; leer lassen, um ihn zu entfernen")
    @app_commands.checks.has_permissions(ban_members=True)
    async def channel(self, interaction: discord.Interaction, channel: discord.TextChannel | None = None) -> None:
        guild = interaction.guild
        settings = self.storage.load(guild.id)

        if channel is not None and channel.id == settings["channel_id"]:
            await interaction.response.send_message(f"{channel.mention} ist bereits der Honeypot-Channel.", ephemeral=True)
            return

        # Die Aktualisierungen können dauern, daher zuerst bestätigen.
        await interaction.response.defer(ephemeral=True)
        await self.service.delete_info_message(guild)

        if channel is None:
            if settings["channel_id"] is None:
                await interaction.followup.send("Es ist kein Honeypot-Channel gesetzt.", ephemeral=True)
                return
            self.storage.update(guild.id, channel_id=None, active=False, info_message_id=None, log_thread_id=None)
            await interaction.followup.send(
                "Honeypot-Channel entfernt. Die Überwachung ist beendet.", ephemeral=True
            )
            return

        settings = self.storage.update(guild.id, channel_id=channel.id, info_message_id=None, log_thread_id=None)
        text = f"Honeypot-Channel gesetzt: {channel.mention}."
        if settings["active"]:
            if await self.service.update_info_message(guild, setup=True) is None:
                text += " Die Infonachricht konnte dort nicht gesendet werden (fehlen dem Bot Rechte?)."
            else:
                text += " Die Infonachricht wurde gesendet."
        else:
            text += " Die Überwachung ist inaktiv; mit `/honeypot start` aktivieren."
        await interaction.followup.send(text, ephemeral=True)

    @staticmethod
    def _unique_roles(*roles: discord.Role | None) -> list[discord.Role]:
        """Übergebene Rollen ohne Duplikate und ohne leere Parameter."""
        unique: dict[int, discord.Role] = {}
        for role in roles:
            if role is not None:
                unique.setdefault(role.id, role)
        return list(unique.values())

    @app_commands.command(name="setrole", description="Fügt Save-Roles hinzu (deren Mitglieder werden nie gebannt).")
    @app_commands.describe(rolle1="Erste Rolle", rolle2="Weitere Rolle", rolle3="Weitere Rolle",
                           rolle4="Weitere Rolle", rolle5="Weitere Rolle")
    @app_commands.checks.has_permissions(ban_members=True)
    async def setrole(
        self,
        interaction: discord.Interaction,
        rolle1: discord.Role,
        rolle2: discord.Role | None = None,
        rolle3: discord.Role | None = None,
        rolle4: discord.Role | None = None,
        rolle5: discord.Role | None = None,
    ) -> None:
        settings = self.storage.load(interaction.guild.id)
        current: list[int] = list(settings["safe_role_ids"])
        added: list[discord.Role] = []
        existing: list[discord.Role] = []
        rejected: list[discord.Role] = []
        for role in self._unique_roles(rolle1, rolle2, rolle3, rolle4, rolle5):
            if role.is_default() or role.managed:
                rejected.append(role)
            elif role.id in current:
                existing.append(role)
            else:
                current.append(role.id)
                added.append(role)

        if added:
            self.storage.update(interaction.guild.id, safe_role_ids=current)

        lines = []
        if added:
            lines.append("Hinzugefügt: " + ", ".join(role.mention for role in added))
        if existing:
            lines.append("Bereits Save-Role: " + ", ".join(role.mention for role in existing))
        if rejected:
            lines.append(
                "Nicht erlaubt (@everyone oder von einer Integration/einem Bot verwaltet): "
                + ", ".join(role.mention for role in rejected)
            )
        await interaction.response.send_message("\n".join(lines), ephemeral=True)

    @app_commands.command(name="removerole", description="Entfernt Save-Roles.")
    @app_commands.describe(rolle1="Erste Rolle", rolle2="Weitere Rolle", rolle3="Weitere Rolle",
                           rolle4="Weitere Rolle", rolle5="Weitere Rolle")
    @app_commands.checks.has_permissions(ban_members=True)
    async def removerole(
        self,
        interaction: discord.Interaction,
        rolle1: discord.Role,
        rolle2: discord.Role | None = None,
        rolle3: discord.Role | None = None,
        rolle4: discord.Role | None = None,
        rolle5: discord.Role | None = None,
    ) -> None:
        settings = self.storage.load(interaction.guild.id)
        current: list[int] = list(settings["safe_role_ids"])
        removed: list[discord.Role] = []
        missing: list[discord.Role] = []
        for role in self._unique_roles(rolle1, rolle2, rolle3, rolle4, rolle5):
            if role.id in current:
                current.remove(role.id)
                removed.append(role)
            else:
                missing.append(role)

        if removed:
            self.storage.update(interaction.guild.id, safe_role_ids=current)

        lines = []
        if removed:
            lines.append("Entfernt: " + ", ".join(role.mention for role in removed))
        if missing:
            lines.append("Keine Save-Role: " + ", ".join(role.mention for role in missing))
        await interaction.response.send_message("\n".join(lines), ephemeral=True)

    @app_commands.command(name="setlanguage", description="Setzt die Sprache der Infonachricht.")
    @app_commands.describe(language="Sprache laut Sprachdatei, z. B. DEUTSCH")
    @app_commands.checks.has_permissions(ban_members=True)
    async def setlanguage(self, interaction: discord.Interaction, language: str) -> None:
        guild = interaction.guild
        names = language_names()
        name = language.strip().upper()
        if name not in names:
            available = ", ".join(names) or "keine"
            await interaction.response.send_message(
                f"Unbekannte Sprache **{language}**. Verfügbar: {available}", ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)
        self.storage.update(guild.id, language=name)
        # Ohne gesetzten Channel passiert hier nichts; sonst wird die Infonachricht angepasst.
        await self.service.update_info_message(guild)
        await interaction.followup.send(f"Sprache auf **{name}** gesetzt.", ephemeral=True)

    @setlanguage.autocomplete("language")
    async def _language_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        current = current.strip().upper()
        return [app_commands.Choice(name=name, value=name) for name in language_names() if current in name][:25]


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Honeypot(bot))
