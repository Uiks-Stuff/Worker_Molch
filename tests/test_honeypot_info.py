"""Tests für HoneypotService.update_info_message."""
from unittest.mock import AsyncMock, MagicMock

import discord
import pytest
from discord.ext import commands

from modules.honeypot.service import HoneypotService
from modules.honeypot.storage import HoneypotStorage

BOT_ID = 999


@pytest.fixture
def storage(tmp_path):
    return HoneypotStorage(tmp_path / "h.json")


@pytest.fixture
def service(storage):
    bot = MagicMock(spec=commands.Bot)
    bot.user = MagicMock(spec=discord.ClientUser)
    bot.user.id = BOT_ID
    return HoneypotService(bot, storage)


def _message(message_id, author_id=BOT_ID, content="alt"):
    message = MagicMock(spec=discord.Message)
    message.id = message_id
    message.author = MagicMock()
    message.author.id = author_id
    message.content = content
    message.edit = AsyncMock()
    return message


def _channel(history=(), sent_id=500):
    channel = MagicMock(spec=discord.TextChannel)
    channel.id = 42
    channel.send = AsyncMock(return_value=_message(sent_id))
    channel.fetch_message = AsyncMock()

    async def _history(limit=None):
        for item in history:
            yield item

    channel.history = _history
    return channel


def _guild(channel, guild_id=1):
    guild = MagicMock(spec=discord.Guild)
    guild.id = guild_id
    guild.get_channel.return_value = channel
    return guild


def _mentions(call):
    return call.kwargs["allowed_mentions"]


async def test_kein_channel_gesetzt_tut_nichts(service, storage):
    guild = _guild(None)
    assert await service.update_info_message(guild, setup=True) is None
    guild.get_channel.assert_not_called()


async def test_channel_existiert_nicht_mehr(service, storage):
    storage.update(1, channel_id=42)
    assert await service.update_info_message(_guild(None), setup=True) is None


async def test_setup_sendet_mit_everyone_ping_und_speichert_id(service, storage):
    storage.update(1, channel_id=42, active=True, ban_count=3)
    channel = _channel()
    await service.update_info_message(_guild(channel), setup=True)
    channel.send.assert_awaited_once()
    text = channel.send.call_args.args[0]
    assert text.startswith("@everyone Hallo!") and text.endswith("Bans: 3")
    assert _mentions(channel.send.call_args).everyone is True
    assert storage.load(1)["info_message_id"] == 500


async def test_ohne_setup_kein_ping(service, storage):
    storage.update(1, channel_id=42, active=True)
    channel = _channel()
    await service.update_info_message(_guild(channel), setup=False)
    assert _mentions(channel.send.call_args).everyone is False


async def test_vorhandene_nachricht_wird_bearbeitet_ohne_ping(service, storage):
    storage.update(1, channel_id=42, active=True, info_message_id=77, ban_count=9)
    channel = _channel()
    existing = _message(77)
    channel.fetch_message.return_value = existing
    await service.update_info_message(_guild(channel), setup=True)
    channel.send.assert_not_called()
    existing.edit.assert_awaited_once()
    assert existing.edit.call_args.kwargs["content"].endswith("Bans: 9")
    assert _mentions(existing.edit.call_args).everyone is False


async def test_unveraenderte_nachricht_wird_nicht_bearbeitet(service, storage):
    storage.update(1, channel_id=42, active=True, info_message_id=77)
    channel = _channel()
    from modules.honeypot.languages import get_language, render_info

    existing = _message(77, content=render_info(get_language("DEUTSCH"), 0, True))
    channel.fetch_message.return_value = existing
    await service.update_info_message(_guild(channel))
    existing.edit.assert_not_called()


async def test_eigene_nachricht_im_verlauf_wird_uebernommen(service, storage):
    storage.update(1, channel_id=42, active=True)
    fremd = _message(1, author_id=123)
    eigene = _message(2)
    channel = _channel(history=[fremd, eigene])
    await service.update_info_message(_guild(channel), setup=True)
    channel.send.assert_not_called()
    eigene.edit.assert_awaited_once()
    assert storage.load(1)["info_message_id"] == 2


async def test_geloeschte_nachricht_wird_ohne_ping_neu_gesendet(service, storage):
    storage.update(1, channel_id=42, active=True, info_message_id=77)
    channel = _channel(sent_id=600)
    channel.fetch_message.side_effect = discord.NotFound(MagicMock(status=404), "weg")
    await service.update_info_message(_guild(channel), setup=True)
    channel.send.assert_awaited_once()
    assert _mentions(channel.send.call_args).everyone is False
    assert storage.load(1)["info_message_id"] == 600


async def test_inaktiv_hat_zusatz_aktiv_nicht(service, storage):
    storage.update(1, channel_id=42, active=False)
    channel = _channel()
    await service.update_info_message(_guild(channel))
    assert channel.send.call_args.args[0].endswith("Honeypot under construction")

    storage.update(1, active=True, info_message_id=None)
    channel = _channel()
    await service.update_info_message(_guild(channel))
    assert "under construction" not in channel.send.call_args.args[0]


async def test_sprache_wird_verwendet_und_entfernte_faellt_auf_deutsch(service, storage):
    storage.update(1, channel_id=42, active=True, language="english")
    channel = _channel()
    await service.update_info_message(_guild(channel))
    assert "Hello!" in channel.send.call_args.args[0]

    storage.update(1, language="ENTFERNT", info_message_id=None)
    channel = _channel()
    await service.update_info_message(_guild(channel))
    assert "Hallo!" in channel.send.call_args.args[0]


async def test_discord_fehler_wird_abgefangen(service, storage):
    storage.update(1, channel_id=42, active=True)
    channel = _channel()
    channel.send.side_effect = discord.Forbidden(MagicMock(status=403), "keine Rechte")
    assert await service.update_info_message(_guild(channel), setup=True) is None
    assert storage.load(1)["info_message_id"] is None
