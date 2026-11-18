"""Integrationstest: kompletter Ablauf mit echtem Cog/Service/Storage und gemockten Discord-Objekten."""
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import discord
import pytest
from discord.ext import commands

from modules.honeypot import cog as cog_module
from modules.honeypot.storage import HoneypotStorage

BOT_ID = 999


class FakeGuild:
    """Minimaler Server mit einem Textchannel; protokolliert Bann, Thread und Infonachricht."""

    def __init__(self):
        self.id = 1
        self.owner_id = 1000
        self.me = MagicMock(spec=discord.Member)
        self.info_message = None
        self.thread = MagicMock(spec=discord.Thread, id=900)
        self.thread.send = AsyncMock()

        self.channel = MagicMock(spec=discord.TextChannel)
        self.channel.id = 42
        self.channel.name = "honeypot"
        self.channel.mention = "<#42>"
        self.channel.guild = self
        self.channel.permissions_for.return_value = discord.Permissions.all()
        self.channel.create_thread = AsyncMock(return_value=self.thread)
        self.channel.send = AsyncMock(side_effect=self._send)
        self.channel.fetch_message = AsyncMock(side_effect=self._fetch)

        self.text_channels = [self.channel]
        self.ban = AsyncMock()
        self.get_role = MagicMock(return_value=None)

    async def _send(self, text, **kwargs):
        self.info_message = MagicMock(spec=discord.Message, id=500, content=text)
        self.info_message.edit = AsyncMock(side_effect=self._edit)
        return self.info_message

    async def _edit(self, content, **kwargs):
        self.info_message.content = content

    async def _fetch(self, message_id):
        return self.info_message

    def get_channel(self, channel_id):
        return self.channel if channel_id == 42 else None

    def get_thread(self, thread_id):
        return self.thread if thread_id == 900 else None


def _bot():
    bot = MagicMock(spec=commands.Bot)
    bot.user = MagicMock(spec=discord.ClientUser, id=BOT_ID)
    return bot


def _command_interaction(guild):
    interaction = MagicMock(spec=discord.Interaction)
    interaction.guild = guild
    interaction.response = MagicMock()
    interaction.response.send_message = AsyncMock()
    interaction.response.defer = AsyncMock()
    interaction.followup = MagicMock()
    interaction.followup.send = AsyncMock()
    return interaction


def _user_message(guild, user_id=7, content="Gratis Nitro!"):
    author = MagicMock(spec=discord.Member)
    author.id = user_id
    author.bot = False
    author.roles = []
    author.guild_permissions = discord.Permissions()
    author.__str__ = lambda self: f"user{user_id}"
    message = MagicMock(spec=discord.Message)
    message.guild = guild
    message.author = author
    message.channel = MagicMock(id=42)
    message.content = content
    message.attachments = []
    message.webhook_id = None
    message.created_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
    message.is_system.return_value = False
    message.delete = AsyncMock()
    return message


@pytest.fixture
def path(tmp_path):
    return tmp_path / "data" / "honeypot.json"


async def test_voller_ablauf_und_neustart(path):
    guild = FakeGuild()
    cog = cog_module.Honeypot(_bot(), HoneypotStorage(path))
    interaction = _command_interaction(guild)

    # start: Channel „honeypot“ wird genutzt, Infonachricht mit Ping, Bans: 0
    await cog.start.callback(cog, interaction)
    assert guild.channel.send.call_args.kwargs["allowed_mentions"].everyone is True
    assert guild.info_message.content.endswith("Bans: 0")

    # Nachricht eines normalen Users -> Bann, Löschen, Log, Zähler, Info
    message = _user_message(guild)
    await cog.on_message(message)
    guild.ban.assert_awaited_once()
    message.delete.assert_awaited_once()
    embed = guild.thread.send.call_args.kwargs["embed"]
    assert {f.name: f.value for f in embed.fields}["User-ID"] == "7"
    assert guild.info_message.content.endswith("Bans: 1")
    assert HoneypotStorage(path).load(1)["ban_count"] == 1

    # Neustart / Reload: neues Cog mit derselben Datei kennt den Zustand
    neu = cog_module.Honeypot(_bot(), HoneypotStorage(path))
    status = _command_interaction(guild)
    await neu.status.callback(neu, status)
    text = status.response.send_message.call_args.args[0]
    assert "aktiv" in text and "inaktiv" not in text
    assert "<#42>" in text and "**Gebannte User:** 1" in text

    # Das neue Cog bannt weiter und zählt weiter; Log-Thread und Infonachricht werden wiederverwendet.
    await neu.on_message(_user_message(guild, user_id=8))
    assert guild.ban.await_count == 2
    assert guild.info_message.content.endswith("Bans: 2")
    guild.channel.create_thread.assert_awaited_once()
    guild.channel.send.assert_awaited_once()  # nur die erste Infonachricht, danach nur edit

    # stop -> keine weiteren Banns
    await neu.stop.callback(neu, _command_interaction(guild))
    assert guild.info_message.content.endswith("Honeypot under construction")
    await neu.on_message(_user_message(guild, user_id=9))
    assert guild.ban.await_count == 2


async def test_save_role_und_moderator_im_ablauf(path):
    guild = FakeGuild()
    cog = cog_module.Honeypot(_bot(), HoneypotStorage(path))
    await cog.start.callback(cog, _command_interaction(guild))

    role = MagicMock(spec=discord.Role, id=50, mention="<@&50>", managed=False)
    role.is_default.return_value = False
    await cog.setrole.callback(cog, _command_interaction(guild), role)

    safe = _user_message(guild, user_id=20)
    safe.author.roles = [MagicMock(id=50)]
    mod = _user_message(guild, user_id=21)
    mod.author.guild_permissions = discord.Permissions(ban_members=True)
    await cog.on_message(safe)
    await cog.on_message(mod)
    guild.ban.assert_not_called()


async def test_kanal_geloescht_im_ablauf(path):
    guild = FakeGuild()
    cog = cog_module.Honeypot(_bot(), HoneypotStorage(path))
    await cog.start.callback(cog, _command_interaction(guild))

    await cog.on_guild_channel_delete(guild.channel)
    settings = HoneypotStorage(path).load(1)
    assert settings["active"] is False and settings["channel_id"] is None
    await cog.on_message(_user_message(guild))
    guild.ban.assert_not_called()
