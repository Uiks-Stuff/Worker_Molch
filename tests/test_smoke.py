"""Smoke-Tests für den bestehenden Code (Core + Modul clear). Keine Discord-Verbindung."""
import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from core.module_manager import ModuleManager, ModuleManagerError


def _manager(tmp_path, enabled=None):
    modules = tmp_path / "modules"
    (modules / "demo").mkdir(parents=True)
    (modules / "demo" / "__init__.py").write_text("")
    (modules / "demo" / "cog.py").write_text("")
    (modules / "unvollstaendig").mkdir()
    config = tmp_path / "modules.json"
    config.write_text(json.dumps({"enabled_modules": enabled or []}))
    bot = MagicMock()
    bot.extensions = {}
    bot.load_extension = AsyncMock()
    bot.unload_extension = AsyncMock()
    bot.sync_application_commands = AsyncMock()
    return ModuleManager(bot, config, modules), bot, config


def test_discover_ignoriert_unvollstaendige_module(tmp_path):
    manager, _, _ = _manager(tmp_path)
    assert manager._discover_modules() == {"demo": "modules.demo.cog"}


def test_unbekanntes_modul_wirft_fehler(tmp_path):
    manager, _, _ = _manager(tmp_path)
    with pytest.raises(ModuleManagerError):
        manager._resolve_module("gibtsnicht")


async def test_enable_und_disable_speichern_config(tmp_path):
    manager, bot, config = _manager(tmp_path)
    assert await manager.enable_module("demo") is True
    assert json.loads(config.read_text())["enabled_modules"] == ["modules.demo.cog"]
    bot.load_extension.assert_awaited_once_with("modules.demo.cog")
    bot.extensions["modules.demo.cog"] = object()
    assert await manager.disable_module("demo") is True
    assert json.loads(config.read_text())["enabled_modules"] == []


def test_legacy_modulname_wird_erkannt(tmp_path):
    manager, _, _ = _manager(tmp_path, enabled=["modules.demo"])
    assert manager._read_enabled_extensions() == ["modules.demo.cog"]


def test_clear_modul_hat_setup():
    import modules.clear.cog as cog

    assert callable(cog.setup)


def test_main_definiert_ping():
    import main

    assert main.bot.tree.get_command("ping") is not None
