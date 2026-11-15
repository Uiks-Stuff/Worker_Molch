from __future__ import annotations

import logging

import discord
from discord import app_commands
from discord.ext import commands

from core.module_manager import ModuleManager, ModuleManagerError

logger = logging.getLogger("discordbot.module_commands")


class ModuleCommands(
    commands.GroupCog,
    group_name="module",
    group_description="Verwaltet die optionalen Bot-Module.",
):
    """Core-Befehle zur Modulverwaltung; dieses Cog ist selbst kein optionales Modul."""

    def __init__(self, module_manager: ModuleManager) -> None:
        self.module_manager = module_manager

    @app_commands.command(name="list", description="Zeigt alle verfügbaren Bot-Module und ihren Status.")
    @app_commands.guild_only()
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.checks.has_permissions(manage_guild=True)
    async def list_modules(self, interaction: discord.Interaction) -> None:
        try:
            statuses = self.module_manager.get_module_statuses()
        except ModuleManagerError as exc:
            await interaction.response.send_message(f"❌ {exc}", ephemeral=True)
            return

        if not statuses:
            await interaction.response.send_message(
                "Es wurden noch keine Module gefunden. Erwartet werden Ordner unter `modules/` "
                "mit einer `__init__.py`- und einer `cog.py`-Datei.",
                ephemeral=True,
            )
            return

        lines: list[str] = []
        for status in statuses:
            if status.enabled and status.loaded:
                state = "🟢 aktiv"
            elif status.enabled and not status.loaded:
                state = "🟠 aktiviert, aber nicht geladen (siehe Bot-Log)"
            else:
                state = "⚪ deaktiviert"
            lines.append(f"**{status.name}** — {state}")

        await interaction.response.send_message(
            "**Verfügbare Bot-Module**\n" + "\n".join(lines),
            ephemeral=True,
        )

    @app_commands.command(name="enable", description="Aktiviert ein Modul und registriert dessen Befehle.")
    @app_commands.describe(modul="Kurzname des Moduls, zum Beispiel clear")
    @app_commands.guild_only()
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.checks.has_permissions(manage_guild=True)
    async def enable_module(self, interaction: discord.Interaction, modul: str) -> None:
        await interaction.response.defer(ephemeral=True, thinking=True)
        try:
            changed = await self.module_manager.enable_module(modul)
            if changed:
                message = f"✅ Modul **{modul}** wurde aktiviert. Seine Slash-Commands wurden synchronisiert."
            else:
                message = f"ℹ️ Modul **{modul}** ist bereits aktiv."
        except ModuleManagerError as exc:
            message = f"❌ {exc}"
        except Exception:
            logger.exception("Unerwarteter Fehler beim Aktivieren von Modul %s", modul)
            message = "❌ Beim Aktivieren ist ein unerwarteter Fehler aufgetreten. Bitte Bot-Log prüfen."
        await interaction.followup.send(message, ephemeral=True)

    @app_commands.command(name="disable", description="Deaktiviert ein Modul und entfernt dessen Befehle.")
    @app_commands.describe(modul="Kurzname des Moduls, zum Beispiel clear")
    @app_commands.guild_only()
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.checks.has_permissions(manage_guild=True)
    async def disable_module(self, interaction: discord.Interaction, modul: str) -> None:
        await interaction.response.defer(ephemeral=True, thinking=True)
        try:
            changed = await self.module_manager.disable_module(modul)
            if changed:
                message = f"✅ Modul **{modul}** wurde deaktiviert. Seine Slash-Commands wurden entfernt."
            else:
                message = f"ℹ️ Modul **{modul}** ist bereits deaktiviert."
        except ModuleManagerError as exc:
            message = f"❌ {exc}"
        except Exception:
            logger.exception("Unerwarteter Fehler beim Deaktivieren von Modul %s", modul)
            message = "❌ Beim Deaktivieren ist ein unerwarteter Fehler aufgetreten. Bitte Bot-Log prüfen."
        await interaction.followup.send(message, ephemeral=True)

    @app_commands.command(name="reload", description="Lädt ein aktives Modul neu, ohne den Bot neu zu starten.")
    @app_commands.describe(modul="Kurzname des aktiven Moduls, zum Beispiel clear")
    @app_commands.guild_only()
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.checks.has_permissions(manage_guild=True)
    async def reload_module(self, interaction: discord.Interaction, modul: str) -> None:
        await interaction.response.defer(ephemeral=True, thinking=True)
        try:
            await self.module_manager.reload_module(modul)
            message = f"✅ Modul **{modul}** wurde neu geladen und seine Slash-Commands wurden synchronisiert."
        except ModuleManagerError as exc:
            message = f"❌ {exc}"
        except Exception:
            logger.exception("Unerwarteter Fehler beim Neuladen von Modul %s", modul)
            message = "❌ Beim Neuladen ist ein unerwarteter Fehler aufgetreten. Bitte Bot-Log prüfen."
        await interaction.followup.send(message, ephemeral=True)

