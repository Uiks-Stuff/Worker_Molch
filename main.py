from __future__ import annotations

import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands

from core.module_commands import ModuleCommands
from core.module_manager import ModuleManager

BASE_DIR = Path(__file__).resolve().parent
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[
        logging.StreamHandler(),
        RotatingFileHandler(
            LOG_DIR / "bot.log",
            maxBytes=5 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        ),
    ],
)

logger = logging.getLogger("discordbot")


class DiscordBot(commands.Bot):
    def __init__(self) -> None:
        intents = discord.Intents.none()
        intents.guilds = True

        super().__init__(
            command_prefix="!",  # Nur als Fallback; wir verwenden Slash-Commands.
            intents=intents,
            allowed_mentions=discord.AllowedMentions.none(),
        )
        self.module_manager = ModuleManager(
            self,
            BASE_DIR / "config" / "modules.json",
            BASE_DIR / "modules",
        )

    async def setup_hook(self) -> None:
        # Dieses Cog gehört zum Core und bleibt verfügbar, selbst wenn alle
        # optionalen Module deaktiviert sind.
        await self.add_cog(ModuleCommands(self.module_manager))

        await self.module_manager.load_enabled_modules()
        await self.sync_application_commands()

    async def sync_application_commands(self) -> None:
        """Synchronisiert Commands bei Start und nach Moduländerungen."""
        guild_id_text = os.getenv("GUILD_ID", "").strip()
        if guild_id_text:
            try:
                guild_id = int(guild_id_text)
            except ValueError as exc:
                raise RuntimeError("GUILD_ID muss eine numerische Discord-Server-ID sein.") from exc

            guild = discord.Object(id=guild_id)
            # Wir verwenden ausschließlich globale Commands, die für den
            # Entwicklungsserver gespiegelt werden. Vor dem Kopieren lokale
            # Spiegel entfernen, damit deaktivierte Modul-Commands verschwinden.
            self.tree.clear_commands(guild=guild)
            self.tree.copy_global_to(guild=guild)
            synced = await self.tree.sync(guild=guild)
            logger.info("%s Slash-Command(s) für Server %s synchronisiert.", len(synced), guild_id)
        else:
            synced = await self.tree.sync()
            logger.warning(
                "%s globale Slash-Command(s) synchronisiert. Für die Entwicklung wird GUILD_ID empfohlen.",
                len(synced),
            )

    async def on_ready(self) -> None:
        logger.info("Bot angemeldet als %s (ID: %s)", self.user, self.user.id if self.user else "unbekannt")


bot = DiscordBot()


@bot.tree.command(name="ping", description="Prüft, ob der Bot erreichbar ist.")
async def ping(interaction: discord.Interaction) -> None:
    latency_ms = round(bot.latency * 1000)
    await interaction.response.send_message(
        f"Pong! Latenz: {latency_ms} ms",
        ephemeral=True,
    )


@bot.tree.error
async def on_app_command_error(
    interaction: discord.Interaction,
    error: app_commands.AppCommandError,
) -> None:
    if isinstance(error, app_commands.MissingPermissions):
        labels = {
            "manage_messages": "Nachrichten verwalten",
            "manage_guild": "Server verwalten",
        }
        missing = ", ".join(labels.get(permission, permission) for permission in error.missing_permissions)
        message = f"Dir fehlen die erforderlichen Berechtigungen: **{missing}**."
        logger.warning("Berechtigung fehlt für %s: %s", interaction.user, error)
    elif isinstance(error, app_commands.BotMissingPermissions):
        missing = ", ".join(error.missing_permissions)
        message = f"Mir fehlen notwendige Berechtigungen: **{missing}**."
        logger.warning("Bot-Berechtigung fehlt: %s", missing)
    elif isinstance(error, app_commands.NoPrivateMessage):
        message = "Dieser Befehl kann nur auf einem Discord-Server verwendet werden."
    else:
        original = getattr(error, "original", error)
        logger.error(
            "Unbehandelter Slash-Command-Fehler",
            exc_info=(type(original), original, original.__traceback__),
        )
        message = "Beim Ausführen des Befehls ist ein Fehler aufgetreten. Details stehen im Bot-Log."

    try:
        if interaction.response.is_done():
            await interaction.followup.send(message, ephemeral=True)
        else:
            await interaction.response.send_message(message, ephemeral=True)
    except discord.HTTPException:
        logger.exception("Fehlermeldung konnte nicht an Discord gesendet werden.")


def main() -> None:
    token = os.getenv("DISCORD_TOKEN", "").strip()
    if not token:
        raise RuntimeError("DISCORD_TOKEN fehlt. Bitte die .env-Datei aus .env.example erstellen und ausfüllen.")

    bot.run(token, log_handler=None)


if __name__ == "__main__":
    main()
