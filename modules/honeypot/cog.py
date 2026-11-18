from __future__ import annotations

import logging

import discord
from discord import app_commands
from discord.ext import commands

from .languages import resolve_language, LanguageError
from .storage import HoneypotStorage

logger = logging.getLogger("discordbot.honeypot")

NOT_IMPLEMENTED = "Dieser Befehl ist noch nicht verfügbar."


@app_commands.guild_only()
@app_commands.default_permissions(ban_members=True)
class Honeypot(commands.GroupCog, name="honeypot", description="Honeypot-Channel zum automatischen Bannen von Scammern."):
    def __init__(self, bot: commands.Bot, storage: HoneypotStorage | None = None) -> None:
        self.bot = bot
        self.storage = storage or HoneypotStorage()
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

    @app_commands.command(name="channel", description="Setzt den überwachten Channel.")
    @app_commands.checks.has_permissions(ban_members=True)
    async def channel(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(NOT_IMPLEMENTED, ephemeral=True)

    @app_commands.command(name="setrole", description="Fügt Save-Roles hinzu.")
    @app_commands.checks.has_permissions(ban_members=True)
    async def setrole(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(NOT_IMPLEMENTED, ephemeral=True)

    @app_commands.command(name="removerole", description="Entfernt Save-Roles.")
    @app_commands.checks.has_permissions(ban_members=True)
    async def removerole(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(NOT_IMPLEMENTED, ephemeral=True)

    @app_commands.command(name="setlanguage", description="Setzt die Sprache der Infonachricht.")
    @app_commands.checks.has_permissions(ban_members=True)
    async def setlanguage(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(NOT_IMPLEMENTED, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Honeypot(bot))
