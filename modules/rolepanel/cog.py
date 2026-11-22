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
from .views import RoleButton, build_view

logger = logging.getLogger("discordbot.rolepanel")

NOT_IMPLEMENTED = "Dieser Befehl ist noch nicht verfügbar."
PROVIDER_KEY = "rolepanel"
MAX_USER_ROLES = 25  # Discord erlaubt höchstens 25 Buttons pro Nachricht.

# Rechte des Bots im Willkommenskanal: (Attribut von discord.Permissions, Anzeigename).
CHANNEL_BOT_PERMISSIONS = [
    ("view_channel", "Kanal ansehen"),
    ("send_messages", "Nachrichten senden"),
    ("read_message_history", "Nachrichtenverlauf anzeigen"),
]
# Zusätzlich für `start`: @everyone erwähnen (Ping beim ersten Posten).
START_BOT_PERMISSIONS = CHANNEL_BOT_PERMISSIONS + [("mention_everyone", "@everyone erwähnen")]

# Rollen mit diesen Rechten dürfen nicht per Button vergeben werden: (Attribut, Anzeigename).
DANGEROUS_PERMISSIONS = [
    ("administrator", "Administrator"),
    ("manage_guild", "Server verwalten"),
    ("manage_roles", "Rollen verwalten"),
    ("manage_channels", "Kanäle verwalten"),
    ("ban_members", "Mitglieder bannen"),
    ("kick_members", "Mitglieder kicken"),
    ("manage_messages", "Nachrichten verwalten"),
    ("mention_everyone", "@everyone erwähnen"),
]


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
        self.bot.add_dynamic_items(RoleButton)

    async def cog_unload(self) -> None:
        get_welcome_manager(self.bot).unregister(PROVIDER_KEY)
        self.bot.remove_dynamic_items(RoleButton)

    async def handle_click(self, interaction: discord.Interaction, role_id: int) -> None:
        """Button-Klick: Rolle dem Klickenden geben oder wieder entfernen."""
        guild = interaction.guild
        member = interaction.user
        if guild is None:
            await interaction.response.send_message("Das geht nur auf einem Server.", ephemeral=True)
            return

        role = guild.get_role(role_id)
        if role is None:
            await interaction.response.send_message("Diese Rolle gibt es nicht mehr.", ephemeral=True)
            return
        selectable = role_id in self.storage.load(guild.id)["user_role_ids"]
        if not selectable or self._role_problem(role, interaction, check_user=False):
            await interaction.response.send_message(
                f"{role.mention} ist nicht mehr zur Auswahl freigegeben.", ephemeral=True
            )
            return

        has_role = any(r.id == role_id for r in member.roles)
        try:
            if has_role:
                await member.remove_roles(role, reason="Rolepanel: Rolle per Button entfernt")
            else:
                await member.add_roles(role, reason="Rolepanel: Rolle per Button gewählt")
        except discord.Forbidden:
            logger.warning("Rolle %s konnte auf Guild %s nicht vergeben werden (Forbidden).", role_id, guild.id)
            await interaction.response.send_message(
                f"Ich darf {role.mention} nicht vergeben. Meine Rolle muss über dieser Rolle stehen "
                "und ich brauche das Recht **Rollen verwalten**. Bitte melde das einem Administrator.",
                ephemeral=True,
            )
            return
        except discord.HTTPException:
            logger.exception("Rolle %s konnte auf Guild %s nicht geändert werden.", role_id, guild.id)
            await interaction.response.send_message(
                "Die Rolle konnte gerade nicht geändert werden. Bitte versuche es später erneut.",
                ephemeral=True,
            )
            return

        await interaction.response.send_message(
            f"{'➖' if has_role else '➕'} {role.mention}", ephemeral=True
        )

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
        roles = [role for role in roles if role is not None]
        return render_panel(text, roles), build_view(roles)

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

    @staticmethod
    def _role_problem(
        role: discord.Role, interaction: discord.Interaction, check_user: bool = True
    ) -> str | None:
        """Grund, warum die Rolle nicht wählbar sein darf (Schutz vor Rechteausweitung), sonst None."""
        guild = interaction.guild
        if role.is_default() or role.managed:
            return "@everyone oder von einer Integration/einem Bot verwaltet"
        dangerous = [label for attribute, label in DANGEROUS_PERMISSIONS if getattr(role.permissions, attribute)]
        if dangerous:
            return "hat Admin-/Moderationsrechte (" + ", ".join(dangerous) + ")"
        if role.position >= guild.me.top_role.position:
            return "liegt nicht unter meiner höchsten Rolle"
        if not check_user:
            return None
        user = interaction.user
        privileged = guild.owner_id == user.id or user.guild_permissions.administrator
        if not privileged and role.position >= user.top_role.position:
            return "liegt nicht unter deiner höchsten Rolle"
        return None

    @staticmethod
    def _missing_bot_permissions(
        channel: discord.TextChannel, guild: discord.Guild, required: list[tuple[str, str]]
    ) -> list[str]:
        """Anzeigenamen der Rechte, die der Bot im Kanal braucht, aber nicht hat."""
        permissions = channel.permissions_for(guild.me)
        return [label for attribute, label in required if not getattr(permissions, attribute)]

    async def _refresh_panel(self, guild: discord.Guild) -> None:
        """Aktualisiert die Panel-Nachricht, wenn das Panel aktiv ist."""
        if self.storage.load(guild.id)["active"]:
            await get_welcome_manager(self.bot).refresh(guild, PROVIDER_KEY)

    @app_commands.command(name="userrole", description="Schaltet Rollen in der Auswahl an oder aus.")
    @app_commands.describe(rolle1="Erste Rolle", rolle2="Weitere Rolle", rolle3="Weitere Rolle",
                           rolle4="Weitere Rolle", rolle5="Weitere Rolle")
    async def userrole(
        self,
        interaction: discord.Interaction,
        rolle1: discord.Role,
        rolle2: discord.Role | None = None,
        rolle3: discord.Role | None = None,
        rolle4: discord.Role | None = None,
        rolle5: discord.Role | None = None,
    ) -> None:
        guild = interaction.guild
        current: list[int] = list(self.storage.load(guild.id)["user_role_ids"])
        added: list[discord.Role] = []
        removed: list[discord.Role] = []
        rejected: list[tuple[discord.Role, str]] = []
        too_many: list[discord.Role] = []
        for role in self._unique_roles(rolle1, rolle2, rolle3, rolle4, rolle5):
            if role.id in current:
                # Entfernen ist immer erlaubt (auch für inzwischen unzulässige Rollen).
                current.remove(role.id)
                removed.append(role)
                continue
            problem = self._role_problem(role, interaction)
            if problem:
                rejected.append((role, problem))
            elif len(current) >= MAX_USER_ROLES:
                too_many.append(role)
            else:
                current.append(role.id)
                added.append(role)

        lines = []
        if added:
            lines.append("Hinzugefügt: " + ", ".join(role.mention for role in added))
        if removed:
            lines.append("Entfernt: " + ", ".join(role.mention for role in removed))
        for role, problem in rejected:
            lines.append(f"Nicht erlaubt: {role.mention} – {problem}.")
        if too_many:
            lines.append(
                f"Maximal {MAX_USER_ROLES} Rollen möglich, nicht hinzugefügt: "
                + ", ".join(role.mention for role in too_many)
            )

        if added or removed:
            await interaction.response.defer(ephemeral=True)
            self.storage.update(guild.id, user_role_ids=current)
            await self._refresh_panel(guild)
            await interaction.followup.send("\n".join(lines), ephemeral=True)
        else:
            await interaction.response.send_message("\n".join(lines), ephemeral=True)

    @app_commands.command(name="clear", description="Entfernt alle Rollen aus der Auswahl.")
    async def clear(self, interaction: discord.Interaction) -> None:
        guild = interaction.guild
        if not self.storage.load(guild.id)["user_role_ids"]:
            await interaction.response.send_message("Die Auswahl ist bereits leer.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        self.storage.update(guild.id, user_role_ids=[])
        await self._refresh_panel(guild)
        await interaction.followup.send("Alle Rollen wurden aus der Auswahl entfernt.", ephemeral=True)

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
    @app_commands.describe(channel="Neuer Willkommenskanal")
    async def channel(self, interaction: discord.Interaction, channel: discord.TextChannel) -> None:
        guild = interaction.guild
        manager = get_welcome_manager(self.bot)
        current = manager.get_channel(guild)
        if current is not None and current.id == channel.id:
            await interaction.response.send_message(
                f"{channel.mention} ist bereits der Willkommenskanal.", ephemeral=True
            )
            return

        missing = self._missing_bot_permissions(channel, guild, CHANNEL_BOT_PERMISSIONS)
        if missing:
            await interaction.response.send_message(
                f"Mir fehlen in {channel.mention} diese Rechte: **{', '.join(missing)}**. "
                "Der Willkommenskanal wurde nicht geändert.",
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True)
        # Bereits gepostete Nachrichten aller Module wandern ohne Ping in den neuen Kanal.
        await manager.move_channel(guild, channel)
        await interaction.followup.send(f"Willkommenskanal ist jetzt {channel.mention}.", ephemeral=True)

    @app_commands.command(name="start", description="Postet die Rollenauswahl im Willkommenskanal.")
    async def start(self, interaction: discord.Interaction) -> None:
        await self._not_implemented(interaction)

    @app_commands.command(name="stop", description="Entfernt die Rollenauswahl-Nachricht.")
    async def stop(self, interaction: discord.Interaction) -> None:
        await self._not_implemented(interaction)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Rolepanel(bot))
