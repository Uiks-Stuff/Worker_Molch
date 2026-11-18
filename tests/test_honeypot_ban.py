"""Tests für die Bann-Logik (on_message / Channel gelöscht)."""
import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import discord
import pytest
from discord.ext import commands

from modules.honeypot import cog as cog_module
from modules.honeypot.service import HoneypotService
from modules.honeypot.storage import HoneypotStorage

CHANNEL_ID = 42
OWNER_ID = 1000


@pytest.fixture
def storage(tmp_path):
    s = HoneypotStorage(tmp_path / "h.json")
    s.update(1, active=True, channel_id=CHANNEL_ID, safe_role_ids=[50])
    return s


@pytest.fixture
def service(storage):
    bot = MagicMock(spec=commands.Bot)
    bot.user = MagicMock(spec=discord.ClientUser, id=999)
    service = HoneypotService(bot, storage)
    service._log_event = AsyncMock()
    service._record_ban = AsyncMock()
    return service


def _member(user_id=7, role_ids=(), ban_members=False, administrator=False, bot=False):
    member = MagicMock(spec=discord.Member)
    member.id = user_id
    member.bot = bot
    member.roles = [MagicMock(id=r) for r in role_ids]
    member.guild_permissions = discord.Permissions(ban_members=ban_members, administrator=administrator)
    member.__str__ = lambda self: f"user{user_id}"
    return member


def _guild():
    guild = MagicMock(spec=discord.Guild)
    guild.id = 1
    guild.owner_id = OWNER_ID
    guild.ban = AsyncMock()
    return guild


def _message(guild, author, channel_id=CHANNEL_ID, content="Gratis Nitro!", webhook_id=None, system=False):
    message = MagicMock(spec=discord.Message)
    message.id = 5
    message.guild = guild
    message.author = author
    message.channel = MagicMock(id=channel_id)
    message.content = content
    message.attachments = []
    message.webhook_id = webhook_id
    message.created_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
    message.is_system.return_value = system
    message.delete = AsyncMock()
    return message


async def test_normaler_user_wird_gebannt(service):
    guild = _guild()
    message = _message(guild, _member())
    assert await service.handle_message(message) is True
    guild.ban.assert_awaited_once()
    assert guild.ban.call_args.args[0] is message.author
    assert guild.ban.call_args.kwargs["delete_message_seconds"] == 3600
    assert "Honeypot" in guild.ban.call_args.kwargs["reason"]


async def test_reihenfolge_bann_loeschen_log_zaehler(service):
    guild = _guild()
    message = _message(guild, _member())
    order = MagicMock()
    order.attach_mock(guild.ban, "ban")
    order.attach_mock(message.delete, "delete")
    order.attach_mock(service._log_event, "log")
    order.attach_mock(service._record_ban, "count")
    await service.handle_message(message)
    assert [c[0] for c in order.mock_calls] == ["ban", "delete", "log", "count"]


async def test_log_bekommt_vorher_gesicherte_daten(service):
    guild = _guild()
    await service.handle_message(_message(guild, _member(user_id=7), content="Hallo"))
    snapshot = service._log_event.call_args.args[1]
    assert (snapshot.user_id, snapshot.user_name, snapshot.content) == (7, "user7", "Hallo")
    assert service._log_event.call_args.kwargs["banned"] is True


async def test_inaktiv_wird_ignoriert(service, storage):
    storage.update(1, active=False)
    guild = _guild()
    assert await service.handle_message(_message(guild, _member())) is False
    guild.ban.assert_not_called()


async def test_anderer_channel_und_thread_werden_ignoriert(service):
    guild = _guild()
    assert await service.handle_message(_message(guild, _member(), channel_id=43)) is False
    thread_message = _message(guild, _member(), channel_id=777)  # z. B. Log-Thread
    assert await service.handle_message(thread_message) is False
    guild.ban.assert_not_called()


async def test_dm_wird_ignoriert(service):
    message = _message(_guild(), _member())
    message.guild = None
    assert await service.handle_message(message) is False


@pytest.mark.parametrize(
    "author_kwargs, message_kwargs",
    [
        ({"bot": True}, {}),
        ({}, {"webhook_id": 123}),
        ({"role_ids": (50,)}, {}),  # Save-Role
        ({"ban_members": True}, {}),  # Moderator
        ({"administrator": True}, {}),
        ({"user_id": OWNER_ID}, {}),  # Servereigentümer
        ({}, {"system": True}),
    ],
)
async def test_ausnahmen_werden_nicht_gebannt(service, author_kwargs, message_kwargs):
    guild = _guild()
    message = _message(guild, _member(**author_kwargs), **message_kwargs)
    assert await service.handle_message(message) is False
    guild.ban.assert_not_called()
    message.delete.assert_not_called()
    service._record_ban.assert_not_called()


async def test_user_mit_fremder_rolle_wird_gebannt(service):
    guild = _guild()
    assert await service.handle_message(_message(guild, _member(role_ids=(51,)))) is True


async def test_zwei_nachrichten_gleichzeitig_ein_bann(service):
    guild = _guild()

    async def langsamer_bann(*args, **kwargs):
        await asyncio.sleep(0.05)

    guild.ban.side_effect = langsamer_bann
    author = _member()
    results = await asyncio.gather(
        service.handle_message(_message(guild, author)),
        service.handle_message(_message(guild, author)),
    )
    assert sorted(results) == [False, True]
    guild.ban.assert_awaited_once()
    service._record_ban.assert_awaited_once()


async def test_nachzuegler_nach_bann_wird_nicht_erneut_gezaehlt(service):
    guild = _guild()
    author = _member()
    await service.handle_message(_message(guild, author))
    assert await service.handle_message(_message(guild, author)) is False
    guild.ban.assert_awaited_once()


async def test_verschiedene_user_werden_beide_gebannt(service):
    guild = _guild()
    await service.handle_message(_message(guild, _member(user_id=7)))
    await service.handle_message(_message(guild, _member(user_id=8)))
    assert guild.ban.await_count == 2


async def test_bann_forbidden_wird_geloggt_nicht_gezaehlt(service):
    guild = _guild()
    guild.ban.side_effect = discord.Forbidden(MagicMock(status=403), "Hierarchie")
    message = _message(guild, _member())
    assert await service.handle_message(message) is False
    message.delete.assert_not_called()
    service._record_ban.assert_not_called()
    assert service._log_event.call_args.kwargs["banned"] is False
    assert "Hierarchie" in service._log_event.call_args.kwargs["error"]


async def test_nachricht_bereits_geloescht_ist_kein_fehler(service):
    guild = _guild()
    message = _message(guild, _member())
    message.delete.side_effect = discord.NotFound(MagicMock(status=404), "weg")
    assert await service.handle_message(message) is True
    service._record_ban.assert_awaited_once()


async def test_loeschen_fehlgeschlagen_zaehlt_trotzdem(service):
    guild = _guild()
    message = _message(guild, _member())
    message.delete.side_effect = discord.HTTPException(MagicMock(status=500), "kaputt")
    assert await service.handle_message(message) is True
    service._record_ban.assert_awaited_once()


async def test_channel_geloescht_setzt_zurueck(service, storage):
    storage.update(1, info_message_id=9, log_thread_id=8, ban_count=3)
    channel = MagicMock(spec=discord.TextChannel, id=CHANNEL_ID)
    channel.guild = _guild()
    assert await service.handle_channel_deleted(channel) is True
    settings = storage.load(1)
    assert settings["active"] is False
    assert settings["channel_id"] is None
    assert settings["info_message_id"] is None and settings["log_thread_id"] is None
    assert settings["ban_count"] == 3


async def test_anderer_channel_geloescht_aendert_nichts(service, storage):
    channel = MagicMock(spec=discord.TextChannel, id=1234)
    channel.guild = _guild()
    assert await service.handle_channel_deleted(channel) is False
    assert storage.load(1)["active"] is True


async def test_cog_listener_leiten_weiter_und_schlucken_fehler(storage):
    cog = cog_module.Honeypot(MagicMock(spec=commands.Bot), storage)
    cog.service.handle_message = AsyncMock(side_effect=RuntimeError("boom"))
    cog.service.handle_channel_deleted = AsyncMock()
    await cog.on_message(MagicMock())  # darf nicht werfen
    channel = MagicMock()
    await cog.on_guild_channel_delete(channel)
    cog.service.handle_channel_deleted.assert_awaited_once_with(channel)
