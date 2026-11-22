from __future__ import annotations

import logging
import re
from typing import Any, Iterable

import discord

logger = logging.getLogger("discordbot.rolepanel")

CUSTOM_ID_PREFIX = "rolepanel:role:"
MAX_BUTTONS = 25
MAX_LABEL_LENGTH = 80
COG_NAME = "rolepanel"


class RoleButton(
    discord.ui.DynamicItem[discord.ui.Button],
    template=r"rolepanel:role:(?P<role_id>[0-9]+)",
):
    """Button, der dem Klickenden eine Rolle gibt oder wieder entfernt.

    Als `DynamicItem` bleibt er nach Neustart oder `/module reload` funktionsfähig,
    weil die Rollen-ID in der `custom_id` steckt.
    """

    def __init__(self, role_id: int, label: str | None = None) -> None:
        super().__init__(
            discord.ui.Button(
                label=(label or str(role_id))[:MAX_LABEL_LENGTH],
                style=discord.ButtonStyle.secondary,
                custom_id=f"{CUSTOM_ID_PREFIX}{role_id}",
            )
        )
        self.role_id = role_id

    @classmethod
    async def from_custom_id(
        cls, interaction: discord.Interaction, item: discord.ui.Item, match: re.Match[str], /
    ) -> "RoleButton":
        return cls(int(match["role_id"]), getattr(item, "label", None))

    async def callback(self, interaction: discord.Interaction) -> None:
        cog: Any = interaction.client.get_cog(COG_NAME)
        if cog is None:
            await interaction.response.send_message(
                "Die Rollenauswahl ist gerade nicht verfügbar.", ephemeral=True
            )
            return
        await cog.handle_click(interaction, self.role_id)


MAX_MESSAGE_LENGTH = 1800  # lässt Platz für 25 Rollen-Erwähnungen (Discord-Limit 2000 Zeichen)


class MessageModal(discord.ui.Modal, title="Nachricht bearbeiten"):
    """Formular für den eigenen Nachrichtentext der aktuellen Sprache."""

    text = discord.ui.TextInput(
        label="Text (leer lassen = Standardtext)",
        style=discord.TextStyle.paragraph,
        required=False,
        max_length=MAX_MESSAGE_LENGTH,
    )

    def __init__(self, cog: Any, current: str) -> None:
        super().__init__()
        self.cog = cog
        self.text.default = current[:MAX_MESSAGE_LENGTH]

    async def on_submit(self, interaction: discord.Interaction) -> None:
        await self.cog.apply_message(interaction, self.text.value or "")

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        logger.error("Fehler im Formular „Nachricht bearbeiten“", exc_info=error)
        if not interaction.response.is_done():
            await interaction.response.send_message(
                "Beim Speichern ist ein Fehler aufgetreten. Details stehen im Bot-Log.", ephemeral=True
            )


def build_view(roles: Iterable[discord.Role]) -> discord.ui.View | None:
    """Baut die View mit einem Button pro Rolle (höchstens 25); ohne Rollen None."""
    view = discord.ui.View(timeout=None)
    for role in list(roles)[:MAX_BUTTONS]:
        view.add_item(RoleButton(role.id, role.name))
    return view if view.children else None
