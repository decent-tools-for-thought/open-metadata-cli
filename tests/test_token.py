from __future__ import annotations

import base64
import json

import pytest

from openmetadata_cli.token import decode_token, format_expiry


def _segment(payload: dict[str, object]) -> str:
    return base64.urlsafe_b64encode(json.dumps(payload).encode("utf-8")).decode("utf-8").rstrip("=")


def test_decode_token_parses_payload() -> None:
    token = f"{_segment({'alg': 'none'})}.{_segment({'sub': 'bot', 'exp': 1700000000})}.sig"
    claims = decode_token(token)
    assert claims["sub"] == "bot"
    assert claims["exp"] == 1700000000


def test_decode_token_rejects_malformed_value() -> None:
    with pytest.raises(ValueError, match="valid JWT"):
        decode_token("not-a-token")


def test_format_expiry_formats_timestamp() -> None:
    assert format_expiry(1700000000).endswith("+00:00")
