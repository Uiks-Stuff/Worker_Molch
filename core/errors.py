from __future__ import annotations

from discord import app_commands


class UserFacingCheckFailure(app_commands.CheckFailure):
    """Fehlgeschlagene Prüfung, deren Text dem Nutzer direkt (ephemeral) angezeigt wird."""
