"""Tests für modules/honeypot/languages.py."""
import pytest

from modules.honeypot import languages as lang

TEXT = """
[deutsch]
 - Hallo Welt
 - Bans: X
 - Baustelle

[English]
 - Hello
 - Bans: X

[LEER]

[NURZEILE]
 - nur eins
"""


@pytest.fixture
def path(tmp_path):
    p = tmp_path / "l.txt"
    p.write_text(TEXT, encoding="utf-8")
    return p


def test_parse_namen_grossgeschrieben_und_leere_abschnitte_entfallen(path):
    assert lang.language_names(path) == ["DEUTSCH", "ENGLISH", "NURZEILE"]


def test_zeilen_ohne_fuehrendes_minus(path):
    assert lang.get_language("deutsch", path) == ["Hallo Welt", "Bans: X", "Baustelle"]


def test_unbekannte_sprache_fehler(path):
    with pytest.raises(lang.LanguageError):
        lang.get_language("KLINGONISCH", path)


def test_resolve_fallback_auf_deutsch(path):
    assert lang.resolve_language("ENTFERNT", path)[0] == "DEUTSCH"
    assert lang.resolve_language("english", path)[0] == "ENGLISH"


def test_resolve_ohne_deutsch_fehler(tmp_path):
    p = tmp_path / "l.txt"
    p.write_text("[ENGLISH]\n - a\n")
    with pytest.raises(lang.LanguageError):
        lang.resolve_language("XYZ", p)


def test_fehlende_datei_ergibt_keine_sprachen(tmp_path):
    assert lang.load_languages(tmp_path / "nix.txt") == {}


def test_render_aktiv_ersetzt_x_nur_als_wort():
    lines = ["Text mit Xylophon", "Bans: X", "Zusatz"]
    assert lang.render_info(lines, 7, active=True) == "Text mit Xylophon\nBans: 7"


def test_render_inaktiv_mit_zusatz():
    assert lang.render_info(["A", "Bans: X", "Baustelle"], 0, active=False) == "A\nBans: 0\nBaustelle"


def test_render_inaktiv_ohne_zeile_3_nutzt_standard(path):
    lines = lang.get_language("english", path)
    assert lang.render_info(lines, 2, active=False).endswith("Honeypot under construction")


def test_render_nur_eine_zeile(path):
    assert lang.render_info(lang.get_language("NURZEILE", path), 1, active=True) == "nur eins"


def test_mitgelieferte_sprachdatei_hat_deutsch_und_englisch():
    names = lang.language_names()
    assert "DEUTSCH" in names and "ENGLISH" in names
    text = lang.render_info(lang.get_language("DEUTSCH"), 12, active=True)
    assert text.startswith("@everyone Hallo!")
    assert text.endswith("Bans: 12")
