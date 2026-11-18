"""Tests für /honeypot setrole und /honeypot removerole."""
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
    return cog_module.Honeypot(MagicMock(spec=commands.Bot), storage)


def _interaction(guild_id=1):
    guild = MagicMock(spec=discord.Guild)
    guild.id = guild_id
    interaction = MagicMock(spec=discord.Interaction)
    interaction.guild = guild
    interaction.response = MagicMock()
    interaction.response.send_message = AsyncMock()
    return interaction


def _role(role_id, default=False, managed=False):
    role = MagicMock(spec=discord.Role)
    role.id = role_id
    role.mention = f"<@&{role_id}>"
    role.managed = managed
    role.is_default.return_value = default
    return role


def _text(interaction):
    return interaction.response.send_message.call_args.args[0]


async def test_setrole_fuegt_hinzu_und_speichert(cog, storage):
    interaction = _interaction()
    await cog.setrole.callback(cog, interaction, _role(10), _role(11))
    assert storage.load(1)["safe_role_ids"] == [10, 11]
    assert "Hinzugefügt" in _text(interaction)
    assert interaction.response.send_message.call_args.kwargs["ephemeral"] is True


async def test_setrole_duplikate_und_bereits_gesetzt(cog, storage):
    storage.update(1, safe_role_ids=[10])
    interaction = _interaction()
    await cog.setrole.callback(cog, interaction, _role(10), _role(12), _role(12))
    assert storage.load(1)["safe_role_ids"] == [10, 12]
    text = _text(interaction)
    assert "Bereits Save-Role: <@&10>" in text
    assert text.count("<@&12>") == 1


async def test_setrole_lehnt_everyone_und_managed_ab(cog, storage):
    interaction = _interaction()
    await cog.setrole.callback(cog, interaction, _role(1, default=True), _role(2, managed=True))
    assert storage.load(1)["safe_role_ids"] == []
    assert "Nicht erlaubt" in _text(interaction)
    assert not storage.path.exists()  # nichts zu speichern


async def test_removerole_entfernt_und_meldet_nicht_gesetzte(cog, storage):
    storage.update(1, safe_role_ids=[10, 11])
    interaction = _interaction()
    await cog.removerole.callback(cog, interaction, _role(10), _role(99))
    assert storage.load(1)["safe_role_ids"] == [11]
    text = _text(interaction)
    assert "Entfernt: <@&10>" in text
    assert "Keine Save-Role: <@&99>" in text


async def test_removerole_gleiche_rolle_doppelt(cog, storage):
    storage.update(1, safe_role_ids=[10])
    interaction = _interaction()
    await cog.removerole.callback(cog, interaction, _role(10), _role(10))
    assert storage.load(1)["safe_role_ids"] == []
    assert "Keine Save-Role" not in _text(interaction)


def test_rollenparameter_rolle1_pflicht_rest_optional(cog):
    for name in ("setrole", "removerole"):
        params = {p.name: p.required for p in cog.app_command.get_command(name).parameters}
        assert params == {"rolle1": True, "rolle2": False, "rolle3": False, "rolle4": False, "rolle5": False}
