from __future__ import annotations

import logging
import re
from pathlib import Path

logger = logging.getLogger("discordbot.honeypot")

LANGUAGES_PATH = Path(__file__).resolve().parent / "languages.txt"
DEFAULT_LANGUAGE = "DEUTSCH"
DEFAULT_UNDER_CONSTRUCTION = "Honeypot under construction"

_SECTION_RE = re.compile(r"^\[(?P<name>[^\]]+)\]\s*$")
_COUNT_RE = re.compile(r"(?<!\w)X(?!\w)")


class LanguageError(Exception):
    """Unbekannte oder unbrauchbare Sprache."""


def parse_languages(text: str) -> dict[str, list[str]]:
    """Parst `[NAME]` + Zeilen ` - …`. Schlüssel sind großgeschrieben; leere Abschnitte entfallen."""
    languages: dict[str, list[str]] = {}
    current: list[str] | None = None
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        match = _SECTION_RE.match(line)
        if match:
            name = match.group("name").strip().upper()
            current = languages.setdefault(name, [])
            continue
        if current is None:
            continue  # Text vor dem ersten Abschnitt ignorieren
        if line.startswith("-"):
            line = line[1:].strip()
        if line:
            current.append(line)
    return {name: lines for name, lines in languages.items() if lines}


def load_languages(path: Path | None = None) -> dict[str, list[str]]:
    """Liest die Sprachdatei bei jedem Aufruf neu (Erweitern ohne Reload)."""
    try:
        text = (Path(path) if path is not None else LANGUAGES_PATH).read_text(encoding="utf-8")
    except OSError:
        logger.exception("Sprachdatei konnte nicht gelesen werden.")
        return {}
    return parse_languages(text)


def language_names(path: Path | None = None) -> list[str]:
    return list(load_languages(path))


def get_language(name: str, path: Path | None = None) -> list[str]:
    """Zeilen der Sprache (Name case-insensitive); unbekannt -> LanguageError."""
    languages = load_languages(path)
    lines = languages.get(name.strip().upper())
    if lines is None:
        raise LanguageError(f"Unbekannte Sprache: {name}. Verfügbar: {', '.join(languages) or 'keine'}")
    return lines


def resolve_language(name: str, path: Path | None = None) -> tuple[str, list[str]]:
    """Wie get_language, fällt bei unbekannter (z. B. entfernter) Sprache auf DEUTSCH zurück."""
    languages = load_languages(path)
    key = name.strip().upper()
    if key in languages:
        return key, languages[key]
    if DEFAULT_LANGUAGE in languages:
        logger.warning("Sprache %s nicht gefunden, Fallback auf %s.", name, DEFAULT_LANGUAGE)
        return DEFAULT_LANGUAGE, languages[DEFAULT_LANGUAGE]
    raise LanguageError(f"Weder Sprache {name} noch {DEFAULT_LANGUAGE} in der Sprachdatei gefunden.")


def render_info(lines: list[str], ban_count: int, active: bool) -> str:
    """Infonachricht: Zeile 1 = Text, Zeile 2 = Ban-Zeile (X = Anzahl), Zeile 3 = Zusatz bei inaktiv."""
    parts = [_COUNT_RE.sub(str(ban_count), line) for line in lines[:2]]
    if not active:
        parts.append(lines[2] if len(lines) > 2 else DEFAULT_UNDER_CONSTRUCTION)
    return "\n".join(parts)
