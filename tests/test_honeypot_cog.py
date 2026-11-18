"""Tests für modules/honeypot/cog.py (Gerüst + status)."""
from unittest.mock import AsyncMock, MagicMock

import discord
import pytest
from discord import app_commands
from discord.ext import commands

from modules.honeypot import cog as cog_module
from modules.honeypot.storage import HoneypotStorage

COMMANDS = {"start", "stop", "status", "channel", "setrole", "removerole", "setlanguage"}


@pytest.fixture
def storage(tmp_path):
    return HoneypotStorage(tmp_path / "h.json")


@pytest.fixture
def cog(storage):
    return cog_module.Honeypot(MagicMock(spec=commands.Bot), storage)


def _interaction(guild_id=1, roles=None):
    guild = MagicMock(spec=discord.Guild)
    guild.id = guild_id
    guild.get_role.side_effect = lambda rid: (roles or {}).get(rid)
    interaction = MagicMock(spec=discord.Interaction)
    interaction.guild = guild
    interaction.response = MagicMock()
    interaction.response.send_message = AsyncMock()
    return interaction


def test_alle_befehle_registriert_und_kleingeschrieben(cog):
    names = {command.name for command in cog.app_command.commands}
    assert names == COMMANDS
    assert all(name == name.lower() for name in names)
    assert cog.app_command.name == "honeypot"


def test_rechte_und_guild_only(cog):
    group = cog.app_command
    assert group.guild_only is True
    assert group.default_permissions.ban_members is True
    for command in group.commands:
        assert command.checks, f"{command.name} ohne Rechteprüfung"


async def test_status_standard(cog):
    interaction = _interaction()
    await cog.status.callback(cog, interaction)
    text = interaction.response.send_message.call_args.args[0]
    assert interaction.response.send_message.call_args.kwargs["ephemeral"] is True
    assert "inaktiv" in text
    assert "nicht gesetzt" in text
    assert "DEUTSCH" in text
    assert "**Gebannte User:** 0" in text


async def test_status_aktiv_mit_rollen_geloeschte_ausgeblendet(cog, storage):
    storage.update(1, active=True, channel_id=42, safe_role_ids=[10, 11], language="ENGLISH", ban_count=5)
    role = MagicMock(spec=discord.Role)
    role.mention = "<@&10>"
    interaction = _interaction(roles={10: role})  # Rolle 11 existiert nicht mehr
    await cog.status.callback(cog, interaction)
    text = interaction.response.send_message.call_args.args[0]
    assert "aktiv" in text and "inaktiv" not in text
    assert "<#42>" in text
    assert "<@&10>" in text and "11" not in text
    assert "ENGLISH" in text
    assert "**Gebannte User:** 5" in text


async def test_status_unbekannte_sprache_faellt_auf_deutsch_zurueck(cog, storage):
    storage.update(1, language="ENTFERNT")
    interaction = _interaction()
    await cog.status.callback(cog, interaction)
    assert "DEUTSCH" in interaction.response.send_message.call_args.args[0]


async def test_setup_registriert_cog():
    bot = MagicMock(spec=commands.Bot)
    bot.add_cog = AsyncMock()
    await cog_module.setup(bot)
    added = bot.add_cog.call_args.args[0]
    assert isinstance(added, cog_module.Honeypot)


def test_modul_wird_vom_manager_gefunden(tmp_path):
    from pathlib import Path

    from core.module_manager import ModuleManager

    root = Path(cog_module.__file__).resolve().parents[1]
    manager = ModuleManager(MagicMock(), tmp_path / "m.json", root)
    assert manager._discover_modules()["honeypot"] == "modules.honeypot.cog"
