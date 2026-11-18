"""Tests für modules/honeypot/storage.py."""
import json

import pytest

from modules.honeypot.storage import DEFAULT_SETTINGS, HoneypotStorage


def test_defaults_bei_fehlender_datei(tmp_path):
    storage = HoneypotStorage(tmp_path / "data" / "honeypot.json")
    assert storage.load(1) == DEFAULT_SETTINGS
    assert not (tmp_path / "data").exists()  # Lesen legt nichts an


def test_defaults_bei_defekter_datei(tmp_path):
    path = tmp_path / "honeypot.json"
    path.write_text("{kaputt")
    assert HoneypotStorage(path).load(1) == DEFAULT_SETTINGS
    path.write_text("[1, 2]")
    assert HoneypotStorage(path).load(1) == DEFAULT_SETTINGS


def test_roundtrip_und_data_wird_angelegt(tmp_path):
    path = tmp_path / "data" / "honeypot.json"
    storage = HoneypotStorage(path)
    storage.update(5, active=True, channel_id=42, safe_role_ids=[7, 8], language="ENGLISH", ban_count=3)
    assert path.exists()
    loaded = HoneypotStorage(path).load(5)
    assert loaded["active"] is True
    assert loaded["channel_id"] == 42
    assert loaded["safe_role_ids"] == [7, 8]
    assert loaded["language"] == "ENGLISH"
    assert loaded["ban_count"] == 3
    assert loaded["info_message_id"] is None


def test_guilds_sind_getrennt(tmp_path):
    storage = HoneypotStorage(tmp_path / "h.json")
    storage.update(1, ban_count=5)
    storage.update(2, ban_count=9)
    assert storage.load(1)["ban_count"] == 5
    assert storage.load(2)["ban_count"] == 9
    assert storage.load(3)["ban_count"] == 0


def test_fehlende_schluessel_werden_ergaenzt_und_unbekannte_ignoriert(tmp_path):
    path = tmp_path / "h.json"
    path.write_text(json.dumps({"1": {"ban_count": 4, "fremd": 1}}))
    loaded = HoneypotStorage(path).load(1)
    assert loaded["ban_count"] == 4
    assert loaded["language"] == "DEUTSCH"
    assert "fremd" not in loaded


def test_load_liefert_unabhaengige_kopie(tmp_path):
    storage = HoneypotStorage(tmp_path / "h.json")
    storage.load(1)["safe_role_ids"].append(99)
    assert storage.load(1)["safe_role_ids"] == []


def test_update_unbekannter_schluessel(tmp_path):
    with pytest.raises(KeyError):
        HoneypotStorage(tmp_path / "h.json").update(1, quatsch=1)


def test_keine_temp_datei_bleibt_liegen(tmp_path):
    storage = HoneypotStorage(tmp_path / "h.json")
    storage.update(1, active=True)
    assert [p.name for p in tmp_path.iterdir()] == ["h.json"]
