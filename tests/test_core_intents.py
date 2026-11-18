"""Tests für die Core-Intents und Fehlertexte in main.py."""
from unittest.mock import AsyncMock, MagicMock

import discord
from discord import app_commands

import main


def test_intents_enthalten_nachrichten_und_inhalt():
    intents = main.bot.intents
    assert intents.guilds
    assert intents.guild_messages
    assert intents.message_content
    assert not intents.members


async def test_fehlertext_ban_members_label():
    interaction = MagicMock(spec=discord.Interaction)
    interaction.response = MagicMock()
    interaction.response.is_done.return_value = False
    interaction.response.send_message = AsyncMock()
    error = app_commands.MissingPermissions(["ban_members"])
    await main.on_app_command_error(interaction, error)
    text = interaction.response.send_message.call_args.args[0]
    assert "Mitglieder bannen" in text
    assert "ban_members" not in text
