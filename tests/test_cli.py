from __future__ import annotations

import io
import json
from contextlib import redirect_stdout
from unittest.mock import patch

from openmetadata_cli.cli import build_parser, main, parse_key_values


def test_parse_key_values_rejects_invalid_pair() -> None:
    try:
        parse_key_values(["broken"])
    except ValueError as exc:
        assert "Invalid key=value pair" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_raw_command_emits_json_payload() -> None:
    payload = {"data": [{"id": "1"}]}

    with patch("openmetadata_cli.cli.resolve_client") as resolve_client:
        resolve_client.return_value.raw.return_value = payload
        output = io.StringIO()
        with redirect_stdout(output):
            exit_code = main(["--json", "raw", "/users", "--param", "limit=1"])

    assert exit_code == 0
    assert json.loads(output.getvalue()) == payload


def test_login_parser_defaults_profile_name() -> None:
    parser = build_parser()
    args = parser.parse_args(["login", "--host", "https://metadata.example", "--token", "abc"])
    assert args.login_profile == "default"
