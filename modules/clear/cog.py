from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import timedelta
from typing import Awaitable, Callable

import discord
from discord import app_commands
from discord.ext import commands

logger = logging.getLogger("discordbot.modules.clear")

BATCH_SIZE = 100
MAX_AMOUNT = 100_000

ProgressCallback = Callable[[int, int, int, int], Awaitable[None]]


@dataclass
class ClearResult:
    scanned: int = 0
    matched: int = 0
    deleted: int = 0
    failed: int = 0


async def _delete_one(message: discord.Message, reason: str) -> tuple[int, int]:
    try:
        await message.delete(reason=reason)
        return 1, 0
    except discord.NotFound:
        # Die Nachricht wurde zwischenzeitlich bereits entfernt.
        return 1, 0
    except discord.Forbidden:
        raise
    except discord.HTTPException:
        logger.warning("Einzelne Nachricht konnte nicht gelöscht werden (ID %s).", message.id)
        return 0, 1


async def _delete_batch(
    channel: discord.TextChannel | discord.Thread,
    messages: list[discord.Message],
    reason: str,
) -> tuple[int, int]:
    if not messages:
        return 0, 0

    cutoff = discord.utils.utcnow() - timedelta(days=14)
    recent = [message for message in messages if message.created_at >= cutoff]
    old = [message for message in messages if message.created_at < cutoff]

    deleted = 0
    failed = 0

    # Ältere Nachrichten müssen einzeln gelöscht werden. Discord erlaubt sie nicht
    # in der Bulk-Delete-API.
    for message in old:
        success, failure = await _delete_one(message, reason)
        deleted += success
        failed += failure

    # Neue Nachrichten können in Gruppen von höchstens 100 gelöscht werden.
    for start in range(0, len(recent), BATCH_SIZE):
        chunk = recent[start : start + BATCH_SIZE]
        if len(chunk) == 1:
            success, failure = await _delete_one(chunk[0], reason)
            deleted += success
            failed += failure
            continue

        try:
            await channel.delete_messages(chunk, reason=reason)
            deleted += len(chunk)
        except discord.Forbidden:
            raise
        except discord.HTTPException:
            # Falls die Sammellöschung aus einem anderen API-Grund scheitert,
            # versuchen wir die Nachrichten einzeln. Das ist langsamer, aber robuster.
            logger.warning("Sammellöschung fehlgeschlagen; versuche Einzel-Löschung.")
            for message in chunk:
                success, failure = await _delete_one(message, reason)
                deleted += success
                failed += failure

    return deleted, failed


async def clear_history(
    channel: discord.TextChannel | discord.Thread,
    actor: discord.Member,
    amount: int | None,
    member: discord.Member | None,
    progress: ProgressCallback,
) -> ClearResult:
    result = ClearResult()
    batch: list[discord.Message] = []
    reason = f"/clear ausgeführt von {actor} (ID: {actor.id})"
    loop = asyncio.get_running_loop()
    last_progress = loop.time()

    async for message in channel.history(limit=None, oldest_first=False):
        result.scanned += 1

        if member is None or message.author.id == member.id:
            batch.append(message)
            result.matched += 1

        reached_limit = amount is not None and result.matched >= amount
        batch_full = len(batch) >= BATCH_SIZE

        if batch_full or (reached_limit and batch):
            deleted, failed = await _delete_batch(channel, batch, reason)
            result.deleted += deleted
            result.failed += failed
            batch.clear()
            await progress(result.scanned, result.matched, result.deleted, result.failed)
            last_progress = loop.time()

        if reached_limit:
            break

        # Auch bei einer seltenen Zielperson mit wenigen Nachrichten soll sichtbar
        # bleiben, dass die Suche im Verlauf noch läuft.
        if result.scanned % 1000 == 0 and loop.time() - last_progress >= 3:
            await progress(result.scanned, result.matched, result.deleted, result.failed)
            last_progress = loop.time()

    if batch:
        deleted, failed = await _delete_batch(channel, batch, reason)
        result.deleted += deleted
        result.failed += failed
        await progress(result.scanned, result.matched, result.deleted, result.failed)

    return result


def describe_target(amount: int | None, member: discord.Member | None) -> str:
    if amount is None and member is None:
        return "den **gesamten Nachrichtenverlauf** dieses Kanals"
    if amount is not None and member is None:
        return f"die **letzten {amount} Nachrichten** dieses Kanals"
    if amount is None and member is not None:
        return f"**alle Nachrichten von {member.mention}** in diesem Kanal"
    return f"die **letzten {amount} Nachrichten von {member.mention}** in diesem Kanal"


class ClearConfirmView(discord.ui.View):
    def __init__(
        self,
        cog: "Clear",
        invoker_id: int,
        channel: discord.TextChannel | discord.Thread,
        amount: int | None,
        member: discord.Member | None,
    ) -> None:
        super().__init__(timeout=120)
        self.cog = cog
        self.invoker_id = invoker_id
        self.channel = channel
        self.amount = amount
        self.member = member
        self.message: discord.InteractionMessage | None = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.invoker_id:
            await interaction.response.send_message(
                "Nur die Person, die `/clear` gestartet hat, kann diese Auswahl bestätigen.",
                ephemeral=True,
            )
            return False
        return True

    async def on_timeout(self) -> None:
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                item.disabled = True
        if self.message is not None:
            try:
                await self.message.edit(
                    content="Die Bestätigung ist abgelaufen. Es wurden keine Nachrichten gelöscht.",
                    view=self,
                )
            except discord.HTTPException:
                logger.debug("Abgelaufene Clear-Bestätigung konnte nicht aktualisiert werden.")

    @discord.ui.button(label="Löschen bestätigen", style=discord.ButtonStyle.danger)
    async def confirm(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                item.disabled = True

        await interaction.response.edit_message(
            content="Löschvorgang gestartet. Der Fortschritt wird hier angezeigt …",
            view=self,
        )

        async def update_progress(scanned: int, matched: int, deleted: int, failed: int) -> None:
            content = (
                "**Löschvorgang läuft …**\n"
                f"Nachrichten durchsucht: **{scanned:,}**\n"
                f"Passende Nachrichten gefunden: **{matched:,}**\n"
                f"Gelöscht: **{deleted:,}** · Fehler: **{failed:,}**"
            )
            try:
                await interaction.edit_original_response(content=content, view=self)
            except discord.HTTPException:
                # Bei extrem langen Löschvorgängen kann die Discord-Interaktion
                # ablaufen. Der eigentliche Löschvorgang soll dadurch nicht abbrechen.
                logger.warning("Fortschrittsanzeige der Clear-Interaktion ist nicht mehr erreichbar.")

        try:
            result = await clear_history(
                channel=self.channel,
                actor=interaction.user,  # type: ignore[arg-type]
                amount=self.amount,
                member=self.member,
                progress=update_progress,
            )
            final_text = (
                "**Löschvorgang abgeschlossen.**\n"
                f"Nachrichten durchsucht: **{result.scanned:,}**\n"
                f"Passende Nachrichten: **{result.matched:,}**\n"
                f"Erfolgreich gelöscht: **{result.deleted:,}**\n"
                f"Nicht gelöscht (Fehler): **{result.failed:,}**"
            )
        except discord.Forbidden:
            final_text = (
                "**Löschvorgang abgebrochen:** Discord hat eine Löschung verweigert. "
                "Prüfe, ob der Bot im Kanal noch `Nachrichten verwalten` besitzt. "
                "Bereits gelöschte Nachrichten können nicht wiederhergestellt werden."
            )
            logger.exception("Discord hat eine Clear-Löschung verweigert.")
        except Exception:
            final_text = (
                "**Beim Löschen ist ein unerwarteter Fehler aufgetreten.** "
                "Prüfe das Bot-Log. Bereits gelöschte Nachrichten können nicht wiederhergestellt werden."
            )
            logger.exception("Unerwarteter Fehler im /clear-Modul.")

        try:
            await interaction.edit_original_response(content=final_text, view=None)
        except discord.HTTPException:
            logger.warning("Abschlussmeldung für /clear konnte nicht aktualisiert werden.")
        self.stop()

    @discord.ui.button(label="Abbrechen", style=discord.ButtonStyle.secondary)
    async def cancel(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        await interaction.response.edit_message(
            content="Vorgang abgebrochen. Es wurden keine Nachrichten gelöscht.",
            view=None,
        )
        self.stop()


class Clear(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(
        name="clear",
        description="Löscht Nachrichten aus dem aktuellen Textkanal oder Thread.",
    )
    @app_commands.describe(
        anzahl=f"Anzahl der letzten Nachrichten (1 bis {MAX_AMOUNT}); leer = alle",
        benutzer="Optional: nur Nachrichten dieses Mitglieds löschen",
    )
    @app_commands.guild_only()
    @app_commands.default_permissions(manage_messages=True)
    @app_commands.checks.has_permissions(manage_messages=True)
    @app_commands.checks.bot_has_permissions(
        view_channel=True,
        read_message_history=True,
        manage_messages=True,
    )
    async def clear(
        self,
        interaction: discord.Interaction,
        anzahl: app_commands.Range[int, 1, MAX_AMOUNT] | None = None,
        benutzer: discord.Member | None = None,
    ) -> None:
        channel = interaction.channel
        if not isinstance(channel, (discord.TextChannel, discord.Thread)):
            await interaction.response.send_message(
                "`/clear` funktioniert nur in normalen Textkanälen und Threads.",
                ephemeral=True,
            )
            return

        target = describe_target(anzahl, benutzer)
        warning = (
            f"**Achtung: unwiderrufliche Löschung!**\n"
            f"Es werden {target}.\n\n"
            "Bitte bestätige den Vorgang. Die Bestätigung läuft nach 2 Minuten ab."
        )
        view = ClearConfirmView(
            cog=self,
            invoker_id=interaction.user.id,
            channel=channel,
            amount=anzahl,
            member=benutzer,
        )
        await interaction.response.send_message(warning, view=view, ephemeral=True)
        view.message = await interaction.original_response()


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Clear(bot))
