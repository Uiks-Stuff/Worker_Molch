from __future__ import annotations

import logging

import discord
from discord import app_commands
from discord.ext import commands

from .languages import resolve_language, LanguageError
from .service import HoneypotService
from .storage import HoneypotStorage

logger = logging.getLogger("discordbot.honeypot")

NOT_IMPLEMENTED = "Dieser Befehl ist noch nicht verfügbar."


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
    @app_commands.command(name="start", description="Startet die Überwachung.")
    @app_commands.checks.has_permissions(ban_members=True)
    async def start(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(NOT_IMPLEMENTED, ephemeral=True)

    @app_commands.command(name="stop", description="Beendet die Überwachung.")
    @app_commands.checks.has_permissions(ban_members=True)
    async def stop(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(NOT_IMPLEMENTED, ephemeral=True)

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
    @app_commands.checks.has_permissions(ban_members=True)
    async def setlanguage(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(NOT_IMPLEMENTED, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Honeypot(bot))
