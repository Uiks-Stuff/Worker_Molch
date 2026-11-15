from __future__ import annotations

import asyncio
import importlib
import json
import logging
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from discord.ext import commands

logger = logging.getLogger("discordbot.modules")
MODULE_SLUG_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,31}$")


class ModuleManagerError(RuntimeError):
    """Fehler, die bei der Verwaltung von Bot-Modulen verständlich gemeldet werden können."""


@dataclass(frozen=True)
class ModuleStatus:
    name: str
    extension: str
    enabled: bool
    loaded: bool


class ModuleManager:
    """Entdeckt, lädt und verwaltet optionale Extensions unter modules/<name>/cog.py."""

    def __init__(
        self,
        bot: commands.Bot,
        config_path: Path,
        modules_dir: Path,
    ) -> None:
        self.bot = bot
        self.config_path = config_path
        self.modules_dir = modules_dir
        self._lock = asyncio.Lock()

    def _discover_modules(self) -> dict[str, str]:
        """Gibt {Kurzname: Extension-Pfad} für vorhandene Modulordner zurück."""
        # Wichtig, wenn während der Laufzeit ein neuer Modulordner über den
        # Docker-Bind-Mount auf dem Host angelegt wurde.
        importlib.invalidate_caches()
        available: dict[str, str] = {}
        if not self.modules_dir.is_dir():
            return available

        for module_dir in sorted(self.modules_dir.iterdir(), key=lambda item: item.name.casefold()):
            if not module_dir.is_dir() or not MODULE_SLUG_PATTERN.fullmatch(module_dir.name):
                continue
            if not (module_dir / "__init__.py").is_file():
                continue
            if not (module_dir / "cog.py").is_file():
                continue
            available[module_dir.name] = f"modules.{module_dir.name}.cog"

        return available

    def _read_config(self) -> dict[str, Any]:
        if not self.config_path.is_file():
            raise ModuleManagerError(f"Modulkonfiguration fehlt: {self.config_path}")

        try:
            with self.config_path.open("r", encoding="utf-8") as file:
                config = json.load(file)
        except (OSError, json.JSONDecodeError) as exc:
            raise ModuleManagerError(f"Modulkonfiguration kann nicht gelesen werden: {exc}") from exc

        if not isinstance(config, dict):
            raise ModuleManagerError("config/modules.json muss ein JSON-Objekt enthalten.")
        return config

    def _canonical_extension(self, value: str, available: dict[str, str]) -> str:
        """Unterstützt Kurzname, aktuellen Extension-Pfad und den alten modules.<name>-Pfad."""
        if value in available:
            return available[value]
        if value in available.values():
            return value
        if value.startswith("modules."):
            legacy_slug = value.removeprefix("modules.")
            if legacy_slug in available:
                return available[legacy_slug]
        raise ModuleManagerError(
            f"Unbekanntes oder nicht vollständiges Modul '{value}'. "
            "Erwartet wird ein vorhandenes Modul mit modules/<name>/cog.py."
        )

    def _read_enabled_extensions(self) -> list[str]:
        config = self._read_config()
        raw_modules = config.get("enabled_modules", [])
        if not isinstance(raw_modules, list) or not all(isinstance(item, str) for item in raw_modules):
            raise ModuleManagerError("'enabled_modules' muss eine Liste von Modulnamen sein.")

        available = self._discover_modules()
        canonical: list[str] = []
        for item in raw_modules:
            extension = self._canonical_extension(item, available)
            if extension not in canonical:
                canonical.append(extension)
        return canonical

    def _write_enabled_extensions(self, enabled: list[str]) -> None:
        """Schreibt atomar, damit bei einem Abbruch keine halbe JSON-Datei entsteht."""
        config = self._read_config()
        config["enabled_modules"] = sorted(set(enabled))
        temporary_path = self.config_path.with_name(f".{self.config_path.name}.tmp")

        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with temporary_path.open("w", encoding="utf-8") as file:
                json.dump(config, file, ensure_ascii=False, indent=2)
                file.write("\n")
            os.replace(temporary_path, self.config_path)
        except OSError as exc:
            try:
                temporary_path.unlink(missing_ok=True)
            except OSError:
                logger.warning("Temporäre Modulkonfiguration konnte nicht entfernt werden.")
            raise ModuleManagerError(
                "Modulkonfiguration konnte nicht gespeichert werden. "
                "Prüfe die Schreibrechte des config-Verzeichnisses im Container."
            ) from exc

    def _resolve_module(self, name: str) -> tuple[str, str]:
        cleaned = name.strip()
        available = self._discover_modules()
        try:
            extension = self._canonical_extension(cleaned, available)
        except ModuleManagerError:
            known = ", ".join(sorted(available)) or "keine"
            raise ModuleManagerError(f"Modul '{cleaned}' wurde nicht gefunden. Verfügbar: {known}.")
        slug = next(slug for slug, candidate in available.items() if candidate == extension)
        return slug, extension

    def get_module_statuses(self) -> list[ModuleStatus]:
        enabled_extensions = set(self._read_enabled_extensions())
        available = self._discover_modules()
        return [
            ModuleStatus(
                name=slug,
                extension=extension,
                enabled=extension in enabled_extensions,
                loaded=extension in self.bot.extensions,
            )
            for slug, extension in available.items()
        ]

    async def _sync_application_commands(self) -> None:
        sync_method = getattr(self.bot, "sync_application_commands", None)
        if sync_method is None:
            raise ModuleManagerError("Die Bot-interne Slash-Command-Synchronisierung ist nicht verfügbar.")
        await sync_method()

    async def load_enabled_modules(self) -> None:
        """Lädt Startmodule. Ein defektes optionales Modul soll den Core nicht stoppen."""
        for extension in self._read_enabled_extensions():
            try:
                await self.bot.load_extension(extension)
                logger.info("Modul geladen: %s", extension)
            except Exception:
                logger.exception("Modul konnte beim Start nicht geladen werden: %s", extension)

    async def enable_module(self, name: str) -> bool:
        async with self._lock:
            slug, extension = self._resolve_module(name)
            old_enabled = self._read_enabled_extensions()
            was_loaded = extension in self.bot.extensions

            if extension in old_enabled and was_loaded:
                return False

            try:
                if not was_loaded:
                    await self.bot.load_extension(extension)
                new_enabled = list(old_enabled)
                if extension not in new_enabled:
                    new_enabled.append(extension)
                self._write_enabled_extensions(new_enabled)
                await self._sync_application_commands()
            except Exception as exc:
                # Rollback: Beide Änderungen werden unabhängig zurückgenommen,
                # damit ein Schreibfehler das Entladen nicht verhindert (und umgekehrt).
                try:
                    self._write_enabled_extensions(old_enabled)
                except Exception:
                    logger.exception("Konfigurations-Rollback für %s schlug fehl.", slug)
                if not was_loaded and extension in self.bot.extensions:
                    try:
                        await self.bot.unload_extension(extension)
                    except Exception:
                        logger.exception("Extension-Rollback für %s schlug fehl.", slug)
                if isinstance(exc, ModuleManagerError):
                    raise
                raise ModuleManagerError(f"Modul '{slug}' konnte nicht aktiviert werden: {exc}") from exc

            logger.info("Modul aktiviert: %s", extension)
            return True

    async def disable_module(self, name: str) -> bool:
        async with self._lock:
            slug, extension = self._resolve_module(name)
            old_enabled = self._read_enabled_extensions()
            was_loaded = extension in self.bot.extensions

            if extension not in old_enabled and not was_loaded:
                return False

            try:
                if was_loaded:
                    await self.bot.unload_extension(extension)
                new_enabled = [item for item in old_enabled if item != extension]
                self._write_enabled_extensions(new_enabled)
                await self._sync_application_commands()
            except Exception as exc:
                # Rollback: Konfiguration und geladenen Zustand unabhängig restaurieren.
                try:
                    self._write_enabled_extensions(old_enabled)
                except Exception:
                    logger.exception("Konfigurations-Rollback für %s schlug fehl.", slug)
                if was_loaded and extension not in self.bot.extensions:
                    try:
                        await self.bot.load_extension(extension)
                    except Exception:
                        logger.exception("Extension-Rollback für %s schlug fehl.", slug)
                if isinstance(exc, ModuleManagerError):
                    raise
                raise ModuleManagerError(f"Modul '{slug}' konnte nicht deaktiviert werden: {exc}") from exc

            logger.info("Modul deaktiviert: %s", extension)
            return True

    async def reload_module(self, name: str) -> None:
        async with self._lock:
            slug, extension = self._resolve_module(name)
            if extension not in self.bot.extensions:
                raise ModuleManagerError(
                    f"Modul '{slug}' ist derzeit nicht geladen. Aktiviere es zuerst mit `/module enable`."
                )

            try:
                await self.bot.reload_extension(extension)
                await self._sync_application_commands()
            except Exception as exc:
                logger.exception("Modul-Neuladen fehlgeschlagen: %s", extension)
                raise ModuleManagerError(f"Modul '{slug}' konnte nicht neu geladen werden: {exc}") from exc

            logger.info("Modul neu geladen: %s", extension)
