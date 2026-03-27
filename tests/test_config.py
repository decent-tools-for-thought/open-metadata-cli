from __future__ import annotations

import json
from pathlib import Path

import pytest

import openmetadata_cli.config as config


def test_save_and_load_profile(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    app_dir = tmp_path / "cfg"
    config_path = app_dir / "config.json"
    monkeypatch.setattr(config, "APP_DIR", app_dir)
    monkeypatch.setattr(config, "CONFIG_PATH", config_path)

    profile = config.save_profile("work", "https://metadata.example/api/v1", " token ")

    assert profile.host == "https://metadata.example"
    assert profile.token == "token"
    assert config_path.exists()
    assert config_path.stat().st_mode & 0o777 == 0o600

    stored = json.loads(config_path.read_text(encoding="utf-8"))
    assert stored["current_profile"] == "work"
    assert stored["profiles"]["work"]["host"] == "https://metadata.example"
    assert stored["profiles"]["work"]["token"] == "token"


def test_delete_profile_updates_current_profile(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    app_dir = tmp_path / "cfg"
    config_path = app_dir / "config.json"
    monkeypatch.setattr(config, "APP_DIR", app_dir)
    monkeypatch.setattr(config, "CONFIG_PATH", config_path)

    config.save_profile("alpha", "https://one.example", "a")
    config.save_profile("beta", "https://two.example", "b")
    config.delete_profile("beta")

    assert config.get_current_profile_name() == "alpha"
    assert config.list_profiles() == ["alpha"]
