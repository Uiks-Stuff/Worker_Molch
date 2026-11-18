"""Tests für /honeypot setlanguage."""
from unittest.mock import AsyncMock, MagicMock

import discord
import pytest
from discord.ext import commands

from modules.honeypot import cog as cog_module
from modules.honeypot.storage import HoneypotStorage


@pytest.fixture
def storage(tmp_path):
    return HoneypotStorage(tmp_path / "h.json")


@pytest.fixture
def cog(storage):
    cog = cog_module.Honeypot(MagicMock(spec=commands.Bot), storage)
    cog.service.update_info_message = AsyncMock(return_value=MagicMock())
    return cog


def _interaction():
    guild = MagicMock(spec=discord.Guild)
    guild.id = 1
    interaction = MagicMock(spec=discord.Interaction)
    interaction.guild = guild
    interaction.response = MagicMock()
    interaction.response.send_message = AsyncMock()
    interaction.response.defer = AsyncMock()
    interaction.followup = MagicMock()
    interaction.followup.send = AsyncMock()
    return interaction


async def test_gueltige_sprache_wird_gespeichert_und_info_aktualisiert(cog, storage):
    interaction = _interaction()
    await cog.setlanguage.callback(cog, interaction, "ENGLISH")
    assert storage.load(1)["language"] == "ENGLISH"
    cog.service.update_info_message.assert_awaited_once()
    assert "ENGLISH" in interaction.followup.send.call_args.args[0]


async def test_kleinschreibung_wird_akzeptiert_und_normalisiert(cog, storage):
    await cog.setlanguage.callback(cog, _interaction(), "english")
    assert storage.load(1)["language"] == "ENGLISH"


async def test_ungueltige_sprache_wird_abgelehnt(cog, storage):
    interaction = _interaction()
    await cog.setlanguage.callback(cog, interaction, "KLINGONISCH")
    text = interaction.response.send_message.call_args.args[0]
    assert "Unbekannte Sprache" in text and "DEUTSCH" in text and "ENGLISH" in text
    assert storage.load(1)["language"] == "DEUTSCH"
    cog.service.update_info_message.assert_not_called()


async def test_autocomplete_liste_und_filter(cog):
    interaction = _interaction()
    alle = await cog._language_autocomplete(interaction, "")
    assert {c.value for c in alle} >= {"DEUTSCH", "ENGLISH"}
    gefiltert = await cog._language_autocomplete(interaction, "eng")
    assert [c.value for c in gefiltert] == ["ENGLISH"]
    assert await cog._language_autocomplete(interaction, "zzz") == []


async def test_nachricht_im_channel_wird_angepasst(storage):
    """Mit echtem Service: Sprachwechsel bearbeitet die vorhandene Infonachricht."""
    bot = MagicMock(spec=commands.Bot)
    bot.user = MagicMock(spec=discord.ClientUser, id=999)
    cog = cog_module.Honeypot(bot, storage)
    storage.update(1, channel_id=10, active=True, info_message_id=77)

    message = MagicMock(spec=discord.Message)
    message.id = 77
    message.content = "alt"
    message.edit = AsyncMock()
    channel = MagicMock(spec=discord.TextChannel)
    channel.fetch_message = AsyncMock(return_value=message)
    interaction = _interaction()
    interaction.guild.get_channel.return_value = channel

    await cog.setlanguage.callback(cog, interaction, "english")
    assert "Hello!" in message.edit.call_args.kwargs["content"]


def test_autocomplete_ist_registriert(cog):
    command = cog.app_command.get_command("setlanguage")
    parameter = next(p for p in command.parameters if p.name == "language")
    assert parameter.autocomplete is True
