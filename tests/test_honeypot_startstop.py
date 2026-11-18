"""Tests für /honeypot start und /honeypot stop."""
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


def _permissions(**fehlend):
    values = {attribute: True for attribute, _ in cog_module.REQUIRED_BOT_PERMISSIONS}
    values.update({name: False for name in fehlend})
    return discord.Permissions(**values)


def _text_channel(channel_id, name="honeypot", permissions=None):
    channel = MagicMock(spec=discord.TextChannel)
    channel.id = channel_id
    channel.name = name
    channel.mention = f"<#{channel_id}>"
    channel.permissions_for.return_value = permissions or _permissions()
    return channel


def _interaction(channels=()):
    guild = MagicMock(spec=discord.Guild)
    guild.id = 1
    guild.me = MagicMock(spec=discord.Member)
    by_id = {c.id: c for c in channels}
    guild.get_channel.side_effect = by_id.get
    guild.text_channels = list(channels)
    guild.create_text_channel = AsyncMock()
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


async def test_start_mit_gesetztem_channel(cog, storage):
    channel = _text_channel(10, name="regeln")
    storage.update(1, channel_id=10)
    interaction = _interaction([channel])
    await cog.start.callback(cog, interaction)
    assert storage.load(1)["active"] is True
    interaction.guild.create_text_channel.assert_not_called()
    assert cog.service.update_info_message.call_args.kwargs == {"setup": True}
    assert "<#10>" in _answer(interaction)


async def test_start_nutzt_vorhandenen_honeypot_channel_case_insensitive(cog, storage):
    andere = _text_channel(5, name="allgemein")
    vorhanden = _text_channel(10, name="HoneyPot")
    interaction = _interaction([andere, vorhanden])
    await cog.start.callback(cog, interaction)
    settings = storage.load(1)
    assert settings["channel_id"] == 10 and settings["active"] is True
    interaction.guild.create_text_channel.assert_not_called()


async def test_start_legt_channel_an_wenn_keiner_existiert(cog, storage):
    neu = _text_channel(20)
    interaction = _interaction([_text_channel(5, name="allgemein")])
    interaction.guild.create_text_channel.return_value = neu
    await cog.start.callback(cog, interaction)
    interaction.guild.create_text_channel.assert_awaited_once()
    assert interaction.guild.create_text_channel.call_args.args[0] == "honeypot"
    settings = storage.load(1)
    assert settings["channel_id"] == 20 and settings["active"] is True


async def test_start_gesetzter_channel_geloescht_faellt_auf_suche_zurueck(cog, storage):
    storage.update(1, channel_id=99, info_message_id=7)
    vorhanden = _text_channel(10)
    interaction = _interaction([vorhanden])
    await cog.start.callback(cog, interaction)
    settings = storage.load(1)
    assert settings["channel_id"] == 10
    assert settings["info_message_id"] is None


async def test_start_forbidden_beim_anlegen(cog, storage):
    interaction = _interaction()
    interaction.guild.create_text_channel.side_effect = discord.Forbidden(MagicMock(status=403), "nein")
    await cog.start.callback(cog, interaction)
    assert "Kanäle verwalten" in _answer(interaction)
    assert storage.load(1)["active"] is False


async def test_start_bereits_aktiv(cog, storage):
    storage.update(1, active=True, channel_id=10)
    interaction = _interaction([_text_channel(10)])
    await cog.start.callback(cog, interaction)
    assert "bereits aktiv" in _answer(interaction)
    cog.service.update_info_message.assert_not_called()


async def test_start_fehlende_bot_rechte(cog, storage):
    channel = _text_channel(10, permissions=_permissions(ban_members=True, manage_messages=True))
    storage.update(1, channel_id=10)
    interaction = _interaction([channel])
    await cog.start.callback(cog, interaction)
    text = _answer(interaction)
    assert "Mitglieder bannen" in text and "Nachrichten verwalten" in text
    assert "Kanal ansehen" not in text
    assert storage.load(1)["active"] is False
    cog.service.update_info_message.assert_not_called()


async def test_start_meldet_fehlgeschlagene_infonachricht(cog, storage):
    cog.service.update_info_message.return_value = None
    storage.update(1, channel_id=10)
    interaction = _interaction([_text_channel(10)])
    await cog.start.callback(cog, interaction)
    assert storage.load(1)["active"] is True
    assert "Infonachricht konnte nicht" in _answer(interaction)


async def test_stop_deaktiviert_und_aktualisiert_info(cog, storage):
    storage.update(1, active=True, channel_id=10)
    interaction = _interaction([_text_channel(10)])
    await cog.stop.callback(cog, interaction)
    assert storage.load(1)["active"] is False
    cog.service.update_info_message.assert_awaited_once()
    assert cog.service.update_info_message.call_args.kwargs == {}  # ohne setup/Ping
    assert "beendet" in _answer(interaction)


async def test_stop_bereits_inaktiv(cog, storage):
    interaction = _interaction()
    await cog.stop.callback(cog, interaction)
    assert "bereits inaktiv" in _answer(interaction)
    cog.service.update_info_message.assert_not_called()


async def test_start_nach_stop_ohne_neuen_ping_ueber_service(storage, tmp_path):
    """Integration mit echtem Service: Nach stop existiert die Nachricht -> start bearbeitet nur."""
    bot = MagicMock(spec=commands.Bot)
    bot.user = MagicMock(spec=discord.ClientUser, id=999)
    cog = cog_module.Honeypot(bot, storage)

    sent = MagicMock(spec=discord.Message)
    sent.id = 500
    sent.content = ""
    sent.edit = AsyncMock()
    channel = _text_channel(10)
    channel.send = AsyncMock(return_value=sent)
    channel.fetch_message = AsyncMock(return_value=sent)
    interaction = _interaction([channel])

    await cog.start.callback(cog, interaction)
    assert channel.send.call_args.kwargs["allowed_mentions"].everyone is True  # erstes Aufsetzen

    await cog.stop.callback(cog, interaction)
    assert sent.edit.call_args.kwargs["content"].endswith("Honeypot under construction")

    sent.edit.reset_mock()
    channel.send.reset_mock()
    await cog.start.callback(cog, interaction)
    channel.send.assert_not_called()
    assert "under construction" not in sent.edit.call_args.kwargs["content"]
    assert sent.edit.call_args.kwargs["allowed_mentions"].everyone is False
