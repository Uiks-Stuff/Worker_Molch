from __future__ import annotations

import copy
import json
import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger("discordbot.rolepanel")

# Projektwurzel: modules/rolepanel/storage.py -> zwei Ebenen höher.
DEFAULT_PATH = Path(__file__).resolve().parents[2] / "data" / "rolepanel.json"

DEFAULT_HIERARCHY = 10

DEFAULT_SETTINGS: dict[str, Any] = {
    "active": False,
    "save_role_ids": [],
    "user_role_ids": [],
    "language": "DEUTSCH",
    # Eigener Nachrichtentext pro Sprache: {"DEUTSCH": "…"}
    "custom_messages": {},
    "hierarchy": DEFAULT_HIERARCHY,
}


class RolepanelStorage:
    """Speichert die Rolepanel-Einstellungen pro Guild als JSON-Datei."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = Path(path) if path is not None else DEFAULT_PATH

    def _read_all(self) -> dict[str, Any]:
        try:
            with self.path.open("r", encoding="utf-8") as file:
                data = json.load(file)
        except FileNotFoundError:
            return {}
        except (OSError, json.JSONDecodeError):
            logger.exception("%s ist nicht lesbar; es werden Standardwerte verwendet.", self.path)
            return {}
        if not isinstance(data, dict):
            logger.error("%s enthält kein JSON-Objekt; es werden Standardwerte verwendet.", self.path)
            return {}
        return data

    def _write_all(self, data: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = self.path.with_name(f".{self.path.name}.tmp")
        with temporary_path.open("w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
            file.write("\n")
            file.flush()
            os.fsync(file.fileno())
        os.replace(temporary_path, self.path)

    def load(self, guild_id: int) -> dict[str, Any]:
        """Liefert die Einstellungen der Guild; fehlende Werte werden mit Standardwerten ergänzt."""
        settings = copy.deepcopy(DEFAULT_SETTINGS)
        stored = self._read_all().get(str(guild_id))
        if isinstance(stored, dict):
            for key in DEFAULT_SETTINGS:
                if key in stored:
                    settings[key] = stored[key]
        if not isinstance(settings["custom_messages"], dict):
            settings["custom_messages"] = {}
        return settings

    def save(self, guild_id: int, settings: dict[str, Any]) -> None:
        """Speichert die Einstellungen der Guild; andere Guilds bleiben unverändert."""
        data = self._read_all()
        data[str(guild_id)] = {
            key: settings.get(key, copy.deepcopy(DEFAULT_SETTINGS[key])) for key in DEFAULT_SETTINGS
        }
        self._write_all(data)

    def update(self, guild_id: int, **changes: Any) -> dict[str, Any]:
        """Ändert einzelne Werte, speichert und gibt die neuen Einstellungen zurück."""
        unknown = set(changes) - set(DEFAULT_SETTINGS)
        if unknown:
            raise KeyError(f"Unbekannte Einstellung(en): {', '.join(sorted(unknown))}")
        settings = self.load(guild_id)
        settings.update(changes)
        self.save(guild_id, settings)
        return settings
