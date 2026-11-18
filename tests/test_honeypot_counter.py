"""Tests für Zähler und Info-Update nach einem Bann (Aufgabe 11)."""
from unittest.mock import AsyncMock, MagicMock

import discord
import pytest
from discord.ext import commands

from modules.honeypot.service import HoneypotService
from modules.honeypot.storage import HoneypotStorage


@pytest.fixture
def storage(tmp_path):
    s = HoneypotStorage(tmp_path / "h.json")
    s.update(1, active=True, channel_id=42, ban_count=4)
    return s


@pytest.fixture
def service(storage):
    bot = MagicMock(spec=commands.Bot)
    service = HoneypotService(bot, storage)
    service._log_event = AsyncMock()
    service.update_info_message = AsyncMock()
    return service


def _guild():
    guild = MagicMock(spec=discord.Guild)
    guild.id = 1
    guild.owner_id = 1000
    guild.ban = AsyncMock()
    return guild


def _message(guild, user_id=7):
    author = MagicMock(spec=discord.Member)
    author.id = user_id
    author.bot = False
    author.roles = []
    author.guild_permissions = discord.Permissions()
    message = MagicMock(spec=discord.Message)
    message.guild = guild
    message.author = author
    message.channel = MagicMock(id=42)
    message.content = "spam"
    message.attachments = []
    message.webhook_id = None
    message.is_system.return_value = False
    message.delete = AsyncMock()
    return message


async def test_zaehler_steigt_und_info_wird_aktualisiert(service, storage):
    guild = _guild()
    await service.handle_message(_message(guild))
    assert storage.load(1)["ban_count"] == 5
    service.update_info_message.assert_awaited_once_with(guild)


async def test_zaehler_nur_bei_erfolgreichem_bann(service, storage):
    guild = _guild()
    guild.ban.side_effect = discord.Forbidden(MagicMock(status=403), "nein")
    await service.handle_message(_message(guild))
    assert storage.load(1)["ban_count"] == 4
    service.update_info_message.assert_not_called()


async def test_mehrere_nachrichten_eines_users_zaehlen_einmal(service, storage):
    guild = _guild()
    await service.handle_message(_message(guild))
    await service.handle_message(_message(guild))
    assert storage.load(1)["ban_count"] == 5


async def test_zwei_user_zaehlen_zweimal(service, storage):
    guild = _guild()
    await service.handle_message(_message(guild, 7))
    await service.handle_message(_message(guild, 8))
    assert storage.load(1)["ban_count"] == 6


async def test_info_fehler_bricht_nicht_ab_zaehler_bleibt(service, storage):
    guild = _guild()
    service.update_info_message.side_effect = RuntimeError("boom")
    assert await service.handle_message(_message(guild)) is True
    assert storage.load(1)["ban_count"] == 5


async def test_speicherfehler_bricht_nicht_ab(service, storage, monkeypatch):
    guild = _guild()
    monkeypatch.setattr(storage, "update", MagicMock(side_effect=OSError("voll")))
    # active/channel_id kommen über load() aus der Datei, nur update schlägt fehl
    assert await service.handle_message(_message(guild)) is True
    service.update_info_message.assert_not_called()
