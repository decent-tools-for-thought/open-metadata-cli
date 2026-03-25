from __future__ import annotations

import json
import urllib.error
from email.message import Message
from unittest.mock import patch

import pytest

from openmetadata_cli.client import OpenMetadataClient, OpenMetadataError


class FakeHTTPError(urllib.error.HTTPError):
    def read(self, n: int = -1) -> bytes:
        del n
        return json.dumps({"message": "bad token"}).encode("utf-8")


def test_base_url_normalizes_api_prefix() -> None:
    client = OpenMetadataClient(host="https://metadata.example", token="secret")
    assert client.base_url == "https://metadata.example/api/v1"


def test_raw_strips_full_api_prefix() -> None:
    client = OpenMetadataClient(host="https://metadata.example", token="secret")

    with patch.object(client, "request", return_value={"ok": True}) as request:
        payload = client.raw("GET", "/api/v1/users", limit=1)

    assert payload == {"ok": True}
    request.assert_called_once_with("GET", "/users", params={"limit": 1})


def test_http_error_is_wrapped() -> None:
    client = OpenMetadataClient(host="https://metadata.example", token="secret")
    headers = Message()
    error = FakeHTTPError(
        url="https://metadata.example/api/v1/users",
        code=401,
        msg="Unauthorized",
        hdrs=headers,
        fp=None,
    )

    with patch("urllib.request.urlopen", side_effect=error):
        with pytest.raises(OpenMetadataError, match="HTTP 401: bad token"):
            client.request("GET", "/users")
