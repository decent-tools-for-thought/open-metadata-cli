from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any


class OpenMetadataError(RuntimeError):
    pass


@dataclass
class OpenMetadataClient:
    host: str
    token: str
    timeout: int = 30

    @property
    def base_url(self) -> str:
        return f"{self.host.rstrip('/')}/api/v1"

    def request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        payload: dict[str, Any] | None = None,
    ) -> Any:
        query = ""
        if params:
            query = "?" + urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
        body = None
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json",
        }
        if payload is not None:
            body = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"
        request = urllib.request.Request(
            url=f"{self.base_url}{path}{query}",
            data=body,
            headers=headers,
            method=method.upper(),
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                raw = response.read().decode("utf-8")
                return json.loads(raw) if raw else None
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            try:
                parsed = json.loads(detail)
                message = parsed.get("message") or parsed
            except json.JSONDecodeError:
                message = detail or exc.reason
            raise OpenMetadataError(f"HTTP {exc.code}: {message}") from exc
        except urllib.error.URLError as exc:
            raise OpenMetadataError(f"Connection error: {exc.reason}") from exc

    def health(self) -> Any:
        return self.request("GET", "/users", params={"limit": 1})

    def get_user_by_name(
        self, name: str, fields: str | None = None, include: str = "non-deleted"
    ) -> Any:
        encoded = urllib.parse.quote(name, safe="")
        return self.request(
            "GET", f"/users/name/{encoded}", params={"fields": fields, "include": include}
        )

    def list_entities(self, entity_path: str, **params: Any) -> Any:
        return self.request("GET", entity_path, params=params)

    def get_entity_by_name(self, entity_path: str, fqn: str, **params: Any) -> Any:
        encoded = urllib.parse.quote(fqn, safe="")
        return self.request("GET", f"{entity_path}/name/{encoded}", params=params)

    def search(self, **params: Any) -> Any:
        return self.request("GET", "/search/query", params=params)

    def raw(self, method: str, path: str, **params: Any) -> Any:
        normalized = path if path.startswith("/") else f"/{path}"
        if normalized.startswith("/api/v1/"):
            normalized = normalized[7:]
        return self.request(method, normalized, params=params)
