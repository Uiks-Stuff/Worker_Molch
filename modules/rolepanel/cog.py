from __future__ import annotations

import logging
from typing import Any

import discord
from discord import app_commands
from discord.ext import commands

from core.errors import UserFacingCheckFailure
from core.welcome_channel import get_welcome_manager

from .languages import LanguageError, resolve_language, render_panel
from .storage import RolepanelStorage

logger = logging.getLogger("discordbot.rolepanel")

NOT_IMPLEMENTED = "Dieser Befehl ist noch nicht verfügbar."
PROVIDER_KEY = "rolepanel"


@app_commands.guild_only()
class Rolepanel(commands.GroupCog, name="rolepanel", description="Rollenauswahl per Button im Willkommenskanal."):
    def __init__(self, bot: commands.Bot, storage: RolepanelStorage | None = None) -> None:
        self.bot = bot
        self.storage = storage or RolepanelStorage()
        super().__init__()

    # ------------------------------------------------------------ Lebenszyklus
    async def cog_load(self) -> None:
        # Als Anbieter im gemeinsamen Willkommenskanal anmelden (überlebt /module reload).
        get_welcome_manager(self.bot).register(PROVIDER_KEY, self.render)

    async def cog_unload(self) -> None:
        get_welcome_manager(self.bot).unregister(PROVIDER_KEY)

    async def render(self, guild: discord.Guild) -> tuple[str, discord.ui.View | None]:
        """Text (und später Buttons) der Panel-Nachricht aus dem gespeicherten Zustand."""
        settings = self.storage.load(guild.id)
        try:
            language, text = resolve_language(settings["language"])
        except LanguageError:
            logger.exception("Keine Sprachdatei-Einträge für das Panel verfügbar.")
            text = ""
            language = settings["language"]
        text = settings["custom_messages"].get(language) or text
        roles = [guild.get_role(role_id) for role_id in settings["user_role_ids"]]
        return render_panel(text, [role for role in roles if role is not None]), None

    # ------------------------------------------------------------ Zugriffsprüfung
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Nur Servereigentümer, Administratoren und Mitglieder mit Save-Role dürfen die Befehle nutzen."""
        user = interaction.user
        guild = interaction.guild
        if guild is None:
            raise app_commands.NoPrivateMessage()
        if guild.owner_id == user.id or user.guild_permissions.administrator:
            return True
        save_role_ids = set(self.storage.load(guild.id)["save_role_ids"])
        if any(role.id in save_role_ids for role in user.roles):
            return True
        raise UserFacingCheckFailure(
            "Dafür brauchst du eine Save-Role des Rolepanels (oder Administrator-Rechte). "
            "Bitte wende dich an einen Administrator."
        )

    # ------------------------------------------------------------ Platzhalter (Aufgaben 8–16)
    async def _not_implemented(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(NOT_IMPLEMENTED, ephemeral=True)

    @staticmethod
    def _unique_roles(*roles: discord.Role | None) -> list[discord.Role]:
        """Übergebene Rollen ohne Duplikate und ohne leere Parameter."""
        unique: dict[int, discord.Role] = {}
        for role in roles:
            if role is not None:
                unique.setdefault(role.id, role)
        return list(unique.values())

    @app_commands.command(name="setrole", description="Fügt Save-Roles hinzu (Zugriff auf die Rolepanel-Befehle).")
    @app_commands.describe(rolle1="Erste Rolle", rolle2="Weitere Rolle", rolle3="Weitere Rolle",
                           rolle4="Weitere Rolle", rolle5="Weitere Rolle")
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
        current: list[int] = list(settings["save_role_ids"])
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
            self.storage.update(interaction.guild.id, save_role_ids=current)

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
        current: list[int] = list(settings["save_role_ids"])
        removed: list[discord.Role] = []
        missing: list[discord.Role] = []
        for role in self._unique_roles(rolle1, rolle2, rolle3, rolle4, rolle5):
            if role.id in current:
                current.remove(role.id)
                removed.append(role)
            else:
                missing.append(role)

        if removed:
            self.storage.update(interaction.guild.id, save_role_ids=current)

        lines = []
        if removed:
            lines.append("Entfernt: " + ", ".join(role.mention for role in removed))
        if missing:
            lines.append("Keine Save-Role: " + ", ".join(role.mention for role in missing))
        await interaction.response.send_message("\n".join(lines), ephemeral=True)

    @app_commands.command(name="userrole", description="Schaltet Rollen in der Auswahl an oder aus.")
    async def userrole(
        self,
        interaction: discord.Interaction,
        rolle1: discord.Role,
        rolle2: discord.Role | None = None,
        rolle3: discord.Role | None = None,
        rolle4: discord.Role | None = None,
        rolle5: discord.Role | None = None,
    ) -> None:
        await self._not_implemented(interaction)

    @app_commands.command(name="clear", description="Entfernt alle Rollen aus der Auswahl.")
    async def clear(self, interaction: discord.Interaction) -> None:
        await self._not_implemented(interaction)

    @app_commands.command(name="setlanguage", description="Setzt die Sprache der Nachricht im Kanal.")
    async def setlanguage(self, interaction: discord.Interaction, language: str) -> None:
        await self._not_implemented(interaction)

    @app_commands.command(name="setmessage", description="Bearbeitet den Text der Nachricht im Kanal.")
    async def setmessage(self, interaction: discord.Interaction) -> None:
        await self._not_implemented(interaction)

    @app_commands.command(name="sethierarchie", description="Setzt die Hierarchieebene des Moduls (Standard 10).")
    async def sethierarchie(
        self, interaction: discord.Interaction, ebene: app_commands.Range[int, 1, 100]
    ) -> None:
        await self._not_implemented(interaction)

    @app_commands.command(name="channel", description="Setzt den gemeinsamen Willkommenskanal.")
    async def channel(self, interaction: discord.Interaction, channel: discord.TextChannel) -> None:
        await self._not_implemented(interaction)

    @app_commands.command(name="start", description="Postet die Rollenauswahl im Willkommenskanal.")
    async def start(self, interaction: discord.Interaction) -> None:
        await self._not_implemented(interaction)

    @app_commands.command(name="stop", description="Entfernt die Rollenauswahl-Nachricht.")
    async def stop(self, interaction: discord.Interaction) -> None:
        await self._not_implemented(interaction)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Rolepanel(bot))
