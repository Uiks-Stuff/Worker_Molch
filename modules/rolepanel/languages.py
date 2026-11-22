from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any, Iterable

logger = logging.getLogger("discordbot.rolepanel")

LANGUAGES_PATH = Path(__file__).resolve().parent / "languages.txt"
DEFAULT_LANGUAGE = "DEUTSCH"

_SECTION_RE = re.compile(r"^\[(?P<name>[^\]]+)\]\s*$")


class LanguageError(Exception):
    """Unbekannte oder unbrauchbare Sprache."""


def parse_languages(text: str) -> dict[str, str]:
    """Parst `[NAME]` + Zeilen ` - …` zum Nachrichtentext je Sprache (Schlüssel großgeschrieben).

    Nur Zeilen mit `-` am Anfang zählen als Text (mehrere Zeilen werden mit Zeilenumbruch verbunden).
    Alles andere (z. B. „Rolle 1“) sind Platzhalter und werden ignoriert. Leere Abschnitte entfallen.
    """
    languages: dict[str, list[str]] = {}
    current: list[str] | None = None
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        match = _SECTION_RE.match(line)
        if match:
            current = languages.setdefault(match.group("name").strip().upper(), [])
            continue
        if current is None or not line.startswith("-"):
            continue
        line = line[1:].strip()
        if line:
            current.append(line)
    return {name: "\n".join(lines) for name, lines in languages.items() if lines}


def load_languages(path: Path | None = None) -> dict[str, str]:
    """Liest die Sprachdatei bei jedem Aufruf neu (Erweitern ohne Reload)."""
    try:
        text = (Path(path) if path is not None else LANGUAGES_PATH).read_text(encoding="utf-8")
    except OSError:
        logger.exception("Sprachdatei konnte nicht gelesen werden.")
        return {}
    return parse_languages(text)


def language_names(path: Path | None = None) -> list[str]:
    return list(load_languages(path))


def get_language(name: str, path: Path | None = None) -> str:
    """Text der Sprache (Name case-insensitive); unbekannt -> LanguageError."""
    languages = load_languages(path)
    text = languages.get(name.strip().upper())
    if text is None:
        raise LanguageError(f"Unbekannte Sprache: {name}. Verfügbar: {', '.join(languages) or 'keine'}")
    return text


def resolve_language(name: str, path: Path | None = None) -> tuple[str, str]:
    """Wie get_language, fällt bei unbekannter (z. B. entfernter) Sprache auf DEUTSCH zurück."""
    languages = load_languages(path)
    key = name.strip().upper()
    if key in languages:
        return key, languages[key]
    if DEFAULT_LANGUAGE in languages:
        logger.warning("Sprache %s nicht gefunden, Fallback auf %s.", name, DEFAULT_LANGUAGE)
        return DEFAULT_LANGUAGE, languages[DEFAULT_LANGUAGE]
    raise LanguageError(f"Weder Sprache {name} noch {DEFAULT_LANGUAGE} in der Sprachdatei gefunden.")


def render_panel(text: str, roles: Iterable[Any]) -> str:
    """Nachrichtentext + Leerzeile + eine Rolle pro Zeile als Erwähnung (ohne Rollen nur der Text)."""
    mentions = [role.mention for role in roles]
    if not mentions:
        return text
    return text + "\n\n" + "\n".join(mentions)
