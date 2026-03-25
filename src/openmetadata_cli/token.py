from __future__ import annotations

import base64
import json
from datetime import UTC, datetime
from typing import Any


def _b64decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def decode_token(token: str) -> dict[str, Any]:
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("Token is not a valid JWT.")
    try:
        payload = json.loads(_b64decode(parts[1]).decode("utf-8"))
    except (ValueError, json.JSONDecodeError) as exc:
        raise ValueError("Token payload is not decodable JSON.") from exc
    return payload


def format_expiry(value: Any) -> str:
    if value in (None, "", 0):
        return "never-or-unspecified"
    try:
        timestamp = int(value)
    except (TypeError, ValueError):
        return str(value)
    return datetime.fromtimestamp(timestamp, tz=UTC).isoformat()
