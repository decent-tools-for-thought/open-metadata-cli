from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

APP_DIR = Path.home() / ".config" / "openmetadata-cli"
CONFIG_PATH = APP_DIR / "config.json"


@dataclass
class Profile:
    name: str
    host: str
    token: str


def _normalize_host(host: str) -> str:
    value = host.strip().rstrip("/")
    if value.endswith("/api"):
        value = value[:-4]
    if value.endswith("/api/v1"):
        value = value[:-7]
    return value


def _default_config() -> dict[str, Any]:
    return {"current_profile": None, "profiles": {}}


def load_config() -> dict[str, Any]:
    if not CONFIG_PATH.exists():
        return _default_config()
    with CONFIG_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def save_config(data: dict[str, Any]) -> None:
    APP_DIR.mkdir(parents=True, exist_ok=True)
    temp_path = CONFIG_PATH.with_suffix(".tmp")
    with temp_path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, sort_keys=True)
        handle.write("\n")
    os.chmod(temp_path, 0o600)
    temp_path.replace(CONFIG_PATH)


def save_profile(name: str, host: str, token: str, make_current: bool = True) -> Profile:
    data = load_config()
    data.setdefault("profiles", {})[name] = {
        "host": _normalize_host(host),
        "token": token.strip(),
    }
    if make_current:
        data["current_profile"] = name
    save_config(data)
    return Profile(name=name, host=_normalize_host(host), token=token.strip())


def list_profiles() -> list[str]:
    data = load_config()
    return sorted(data.get("profiles", {}).keys())


def get_current_profile_name() -> str | None:
    return load_config().get("current_profile")


def get_profile(name: str | None = None) -> Profile:
    data = load_config()
    profile_name = name or data.get("current_profile")
    if not profile_name:
        raise ValueError("No profile selected. Run 'omctl login' first or pass --profile.")
    record = data.get("profiles", {}).get(profile_name)
    if not record:
        raise ValueError(f"Profile '{profile_name}' does not exist.")
    return Profile(name=profile_name, host=record["host"], token=record["token"])


def use_profile(name: str) -> Profile:
    profile = get_profile(name)
    data = load_config()
    data["current_profile"] = profile.name
    save_config(data)
    return profile


def delete_profile(name: str) -> None:
    data = load_config()
    profiles = data.get("profiles", {})
    if name not in profiles:
        raise ValueError(f"Profile '{name}' does not exist.")
    profiles.pop(name)
    if data.get("current_profile") == name:
        data["current_profile"] = next(iter(sorted(profiles)), None)
    save_config(data)


def config_path() -> Path:
    return CONFIG_PATH
