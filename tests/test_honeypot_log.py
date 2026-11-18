"""Tests für den Log-Thread (Aufgabe 12)."""
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import discord
import pytest
from discord.ext import commands

from modules.honeypot.service import LOG_CONTENT_LIMIT, HoneypotService, MessageSnapshot
from modules.honeypot.storage import HoneypotStorage


@pytest.fixture
def storage(tmp_path):
    s = HoneypotStorage(tmp_path / "h.json")
    s.update(1, active=True, channel_id=42)
    return s


@pytest.fixture
def service(storage):
    return HoneypotService(MagicMock(spec=commands.Bot), storage)


def _snapshot(content="Gratis Nitro", attachments=0):
    return MessageSnapshot(
        user_id=7,
        user_name="scammer",
        content=content,
        attachment_count=attachments,
        created_at=datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc),
    )


def _thread(thread_id=900):
    thread = MagicMock(spec=discord.Thread)
    thread.id = thread_id
    thread.send = AsyncMock()
    return thread


def _guild(channel=None, thread=None):
    guild = MagicMock(spec=discord.Guild)
    guild.id = 1
    guild.get_channel.return_value = channel
    guild.get_thread.return_value = thread
    guild.fetch_channel = AsyncMock(side_effect=discord.NotFound(MagicMock(status=404), "weg"))
    return guild


def _channel(new_thread=None):
    channel = MagicMock(spec=discord.TextChannel)
    channel.id = 42
    channel.create_thread = AsyncMock(return_value=new_thread or _thread())
    return channel


def _fields(thread):
    embed = thread.send.call_args.kwargs["embed"]
    return embed, {f.name: f.value for f in embed.fields}


async def test_thread_wird_privat_angelegt_und_id_gespeichert(service, storage):
    thread = _thread(901)
    channel = _channel(thread)
    await service._log_event(_guild(channel), _snapshot(), banned=True)
    kwargs = channel.create_thread.call_args.kwargs
    assert kwargs["name"] == "honeypot-log"
    assert kwargs["type"] == discord.ChannelType.private_thread
    assert kwargs["invitable"] is False
    assert storage.load(1)["log_thread_id"] == 901
    thread.send.assert_awaited_once()


async def test_eintrag_enthaelt_alle_angaben(service):
    thread = _thread()
    channel = _channel(thread)
    await service._log_event(_guild(channel), _snapshot(attachments=2), banned=True)
    embed, fields = _fields(thread)
    assert embed.title == "User gebannt"
    assert fields["User-ID"] == "7"
    assert fields["Name"] == "scammer"
    assert "Honeypot" in fields["Banngrund"]
    assert fields["Nachricht"] == "Gratis Nitro"
    assert "2" in fields["Anhänge"]
    assert "Zeitpunkt" in fields
    assert thread.send.call_args.kwargs["allowed_mentions"].users is False


async def test_vorhandener_thread_wird_ueber_cache_verwendet(service, storage):
    storage.update(1, log_thread_id=900)
    thread = _thread(900)
    channel = _channel()
    await service._log_event(_guild(channel, thread), _snapshot(), banned=True)
    channel.create_thread.assert_not_called()
    thread.send.assert_awaited_once()


async def test_archivierter_thread_wird_per_fetch_geholt_und_weiterverwendet(service, storage):
    storage.update(1, log_thread_id=900)
    thread = _thread(900)
    guild = _guild(_channel(), None)
    guild.fetch_channel = AsyncMock(return_value=thread)
    await service._log_event(guild, _snapshot(), banned=True)
    guild.fetch_channel.assert_awaited_once_with(900)
    guild.get_channel.return_value.create_thread.assert_not_called()
    thread.send.assert_awaited_once()


async def test_geloeschter_thread_wird_neu_erstellt(service, storage):
    storage.update(1, log_thread_id=900)
    neu = _thread(901)
    channel = _channel(neu)
    await service._log_event(_guild(channel, None), _snapshot(), banned=True)  # fetch -> NotFound
    channel.create_thread.assert_awaited_once()
    assert storage.load(1)["log_thread_id"] == 901
    neu.send.assert_awaited_once()


async def test_lange_nachricht_wird_gekuerzt(service):
    thread = _thread()
    await service._log_event(_guild(_channel(thread)), _snapshot(content="a" * 5000), banned=True)
    _, fields = _fields(thread)
    assert len(fields["Nachricht"]) == LOG_CONTENT_LIMIT
    assert fields["Nachricht"].endswith("…")


async def test_leere_nachricht(service):
    thread = _thread()
    await service._log_event(_guild(_channel(thread)), _snapshot(content="", attachments=1), banned=True)
    _, fields = _fields(thread)
    assert fields["Nachricht"] == "(kein Text)"


async def test_fehlgeschlagener_bann_wird_geloggt(service):
    thread = _thread()
    await service._log_event(_guild(_channel(thread)), _snapshot(), banned=False, error="403 Missing Permissions")
    embed, fields = _fields(thread)
    assert embed.title == "Bann fehlgeschlagen"
    assert "403 Missing Permissions" in fields["Banngrund"]


async def test_log_fehler_wird_abgefangen(service):
    thread = _thread()
    thread.send.side_effect = discord.Forbidden(MagicMock(status=403), "nein")
    await service._log_event(_guild(_channel(thread)), _snapshot(), banned=True)  # darf nicht werfen


async def test_thread_erstellen_fehler_wird_abgefangen(service):
    channel = _channel()
    channel.create_thread.side_effect = discord.Forbidden(MagicMock(status=403), "nein")
    await service._log_event(_guild(channel), _snapshot(), banned=True)


async def test_kein_channel_nichts_zu_loggen(service, storage):
    storage.update(1, channel_id=None)
    guild = _guild(None)
    await service._log_event(guild, _snapshot(), banned=True)
    guild.get_thread.assert_not_called()
