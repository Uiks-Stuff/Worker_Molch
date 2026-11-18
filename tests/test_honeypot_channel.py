"""Tests für /honeypot channel."""
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


def _text_channel(channel_id):
    channel = MagicMock(spec=discord.TextChannel)
    channel.id = channel_id
    channel.mention = f"<#{channel_id}>"
    channel.fetch_message = AsyncMock()
    return channel


def _interaction(channels=()):
    guild = MagicMock(spec=discord.Guild)
    guild.id = 1
    by_id = {c.id: c for c in channels}
    guild.get_channel.side_effect = by_id.get
    interaction = MagicMock(spec=discord.Interaction)
    interaction.guild = guild
    interaction.response = MagicMock()
    interaction.response.send_message = AsyncMock()
    interaction.response.defer = AsyncMock()
    interaction.followup = MagicMock()
    interaction.followup.send = AsyncMock()
    return interaction


def _answer(interaction):
    if interaction.followup.send.await_count:
        return interaction.followup.send.call_args.args[0]
    return interaction.response.send_message.call_args.args[0]


async def test_channel_setzen_inaktiv(cog, storage):
    new = _text_channel(10)
    interaction = _interaction([new])
    await cog.channel.callback(cog, interaction, new)
    settings = storage.load(1)
    assert settings["channel_id"] == 10
    assert settings["active"] is False
    cog.service.update_info_message.assert_not_called()
    assert "<#10>" in _answer(interaction) and "inaktiv" in _answer(interaction)


async def test_channel_setzen_aktiv_sendet_info_mit_setup(cog, storage):
    storage.update(1, active=True)
    new = _text_channel(10)
    await cog.channel.callback(cog, _interaction([new]), new)
    cog.service.update_info_message.assert_awaited_once()
    assert cog.service.update_info_message.call_args.kwargs == {"setup": True}


async def test_channel_setzen_aktiv_info_fehlgeschlagen(cog, storage):
    storage.update(1, active=True)
    cog.service.update_info_message.return_value = None
    new = _text_channel(10)
    interaction = _interaction([new])
    await cog.channel.callback(cog, interaction, new)
    assert "nicht gesendet" in _answer(interaction)


async def test_channel_wechsel_loescht_alte_info_und_setzt_ids_zurueck(cog, storage):
    old, new = _text_channel(5), _text_channel(10)
    old_message = MagicMock(spec=discord.Message)
    old_message.delete = AsyncMock()
    old.fetch_message.return_value = old_message
    storage.update(1, channel_id=5, info_message_id=77, log_thread_id=88, ban_count=4)
    await cog.channel.callback(cog, _interaction([old, new]), new)
    old.fetch_message.assert_awaited_once_with(77)
    old_message.delete.assert_awaited_once()
    settings = storage.load(1)
    assert settings["channel_id"] == 10
    assert settings["info_message_id"] is None
    assert settings["log_thread_id"] is None
    assert settings["ban_count"] == 4  # Zähler bleibt


async def test_alte_info_bereits_geloescht_ist_kein_fehler(cog, storage):
    old, new = _text_channel(5), _text_channel(10)
    old.fetch_message.side_effect = discord.NotFound(MagicMock(status=404), "weg")
    storage.update(1, channel_id=5, info_message_id=77)
    await cog.channel.callback(cog, _interaction([old, new]), new)
    assert storage.load(1)["channel_id"] == 10


async def test_gleicher_channel_aendert_nichts(cog, storage):
    same = _text_channel(10)
    storage.update(1, channel_id=10, active=True, info_message_id=77)
    interaction = _interaction([same])
    await cog.channel.callback(cog, interaction, same)
    assert "bereits" in _answer(interaction)
    assert storage.load(1)["info_message_id"] == 77
    same.fetch_message.assert_not_called()


async def test_channel_entfernen_stoppt_ueberwachung(cog, storage):
    old = _text_channel(5)
    old.fetch_message.return_value = MagicMock(spec=discord.Message, delete=AsyncMock())
    storage.update(1, channel_id=5, active=True, info_message_id=77, log_thread_id=88)
    interaction = _interaction([old])
    await cog.channel.callback(cog, interaction, None)
    settings = storage.load(1)
    assert settings["channel_id"] is None
    assert settings["active"] is False
    assert settings["info_message_id"] is None
    assert settings["log_thread_id"] is None
    assert "entfernt" in _answer(interaction)


async def test_channel_entfernen_ohne_gesetzten_channel(cog, storage):
    interaction = _interaction()
    await cog.channel.callback(cog, interaction, None)
    assert "kein Honeypot-Channel" in _answer(interaction)
