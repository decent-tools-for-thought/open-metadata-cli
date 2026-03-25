from __future__ import annotations

import argparse
import getpass
import os
import sys
from typing import Any

from . import __version__
from .client import OpenMetadataClient, OpenMetadataError
from .config import (
    config_path,
    delete_profile,
    get_current_profile_name,
    get_profile,
    list_profiles,
    save_profile,
    use_profile,
)
from .formatting import print_json, print_table
from .token import decode_token, format_expiry

ENTITY_MAP = {
    "table": "/tables",
    "tables": "/tables",
    "user": "/users",
    "users": "/users",
    "team": "/teams",
    "teams": "/teams",
    "database": "/databases",
    "databases": "/databases",
    "pipeline": "/pipelines",
    "pipelines": "/pipelines",
    "dashboard": "/dashboards",
    "dashboards": "/dashboards",
    "topic": "/topics",
    "topics": "/topics",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="omctl", description="OpenMetadata command-line client")
    parser.add_argument("--profile", help="Configuration profile to use")
    parser.add_argument("--json", action="store_true", help="Print full JSON output")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    subparsers = parser.add_subparsers(dest="command", required=True)

    login = subparsers.add_parser("login", help="Store a host and token in a profile")
    login.add_argument("--host", required=True, help="OpenMetadata host, with or without /api")
    login.add_argument(
        "--token", help="JWT token. If omitted, read from prompt or OPENMETADATA_JWT_TOKEN"
    )
    login.add_argument("--profile", dest="login_profile", default="default", help="Profile name")
    login.add_argument("--no-verify", action="store_true", help="Skip credential verification")
    login.set_defaults(func=cmd_login)

    profiles = subparsers.add_parser("profiles", help="Manage stored profiles")
    profiles_sub = profiles.add_subparsers(dest="profiles_command", required=True)
    profiles_list = profiles_sub.add_parser("list", help="List profiles")
    profiles_list.set_defaults(func=cmd_profiles_list)
    profiles_use = profiles_sub.add_parser("use", help="Set current profile")
    profiles_use.add_argument("name")
    profiles_use.set_defaults(func=cmd_profiles_use)
    profiles_delete = profiles_sub.add_parser("delete", help="Delete a profile")
    profiles_delete.add_argument("name")
    profiles_delete.set_defaults(func=cmd_profiles_delete)

    auth = subparsers.add_parser("auth", help="Authentication checks")
    auth_sub = auth.add_subparsers(dest="auth_command", required=True)
    auth_status = auth_sub.add_parser("status", help="Validate stored credentials")
    auth_status.set_defaults(func=cmd_auth_status)

    whoami = subparsers.add_parser("whoami", help="Show the active identity")
    whoami.set_defaults(func=cmd_whoami)

    search = subparsers.add_parser("search", help="Search OpenMetadata entities")
    search.add_argument("query", help="Search query")
    search.add_argument("--index", default="all", help="Search index")
    search.add_argument("--from", dest="offset", type=int, default=0, help="Result offset")
    search.add_argument("--size", type=int, default=10, help="Result count")
    search.add_argument("--sort-field", help="Sort field")
    search.add_argument("--sort-order", choices=["asc", "desc"], help="Sort order")
    search.add_argument("--include-source-fields", help="Comma-separated source fields")
    search.set_defaults(func=cmd_search)

    entity = subparsers.add_parser("entity", help="Generic entity operations")
    entity_sub = entity.add_subparsers(dest="entity_command", required=True)
    entity_list = entity_sub.add_parser("list", help="List entities")
    entity_list.add_argument("kind", choices=sorted(ENTITY_MAP))
    entity_list.add_argument("--limit", type=int, default=10)
    entity_list.add_argument("--fields", help="Comma-separated field names")
    entity_list.add_argument("--include", default="non-deleted")
    entity_list.add_argument(
        "--filter", action="append", default=[], help="Extra query param in key=value form"
    )
    entity_list.set_defaults(func=cmd_entity_list)
    entity_get = entity_sub.add_parser("get", help="Get an entity by fully qualified name")
    entity_get.add_argument("kind", choices=sorted(ENTITY_MAP))
    entity_get.add_argument("name", help="Fully qualified name")
    entity_get.add_argument("--fields", help="Comma-separated field names")
    entity_get.add_argument("--include", default="non-deleted")
    entity_get.set_defaults(func=cmd_entity_get)

    table = subparsers.add_parser("table", help="Convenience commands for tables")
    table_sub = table.add_subparsers(dest="table_command", required=True)
    table_list = table_sub.add_parser("list", help="List tables")
    table_list.add_argument("--limit", type=int, default=10)
    table_list.add_argument("--database")
    table_list.add_argument("--database-schema")
    table_list.add_argument("--fields")
    table_list.add_argument("--include", default="non-deleted")
    table_list.set_defaults(func=cmd_table_list)
    table_get = table_sub.add_parser("get", help="Get table by fully qualified name")
    table_get.add_argument("name")
    table_get.add_argument("--fields")
    table_get.add_argument("--include", default="non-deleted")
    table_get.set_defaults(func=cmd_table_get)

    raw = subparsers.add_parser("raw", help="Call an arbitrary OpenMetadata API path")
    raw.add_argument("path", help="Path relative to /api/v1 or full /api/v1 path")
    raw.add_argument("--method", default="GET", help="HTTP method")
    raw.add_argument("--param", action="append", default=[], help="Query param in key=value form")
    raw.set_defaults(func=cmd_raw)

    return parser


def parse_key_values(items: list[str]) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for item in items:
        if "=" not in item:
            raise ValueError(f"Invalid key=value pair: {item}")
        key, value = item.split("=", 1)
        parsed[key] = value
    return parsed


def resolve_token(cli_token: str | None) -> str:
    token = cli_token or os.environ.get("OPENMETADATA_JWT_TOKEN")
    if token:
        return token.strip()
    return getpass.getpass("OpenMetadata JWT token: ").strip()


def resolve_client(args: argparse.Namespace) -> OpenMetadataClient:
    profile = get_profile(args.profile)
    return OpenMetadataClient(host=profile.host, token=profile.token)


def emit(
    args: argparse.Namespace,
    data: Any,
    rows: list[dict[str, Any]] | None = None,
    columns: list[str] | None = None,
) -> None:
    if args.json or rows is None or columns is None:
        print_json(data)
    else:
        print_table(rows, columns)


def cmd_login(args: argparse.Namespace) -> int:
    token = resolve_token(args.token)
    profile_name = args.login_profile
    host = args.host
    if not args.no_verify:
        client = OpenMetadataClient(host=host, token=token)
        client.health()
    profile = save_profile(profile_name, host, token)
    print(f"Saved profile '{profile.name}' for {profile.host}")
    print(f"Config: {config_path()}")
    return 0


def cmd_profiles_list(args: argparse.Namespace) -> int:
    current = get_current_profile_name()
    rows = [{"name": name, "current": "*" if name == current else ""} for name in list_profiles()]
    emit(
        args, {"current_profile": current, "profiles": rows}, rows=rows, columns=["current", "name"]
    )
    return 0


def cmd_profiles_use(args: argparse.Namespace) -> int:
    profile = use_profile(args.name)
    print(f"Current profile: {profile.name}")
    return 0


def cmd_profiles_delete(args: argparse.Namespace) -> int:
    delete_profile(args.name)
    print(f"Deleted profile: {args.name}")
    return 0


def cmd_auth_status(args: argparse.Namespace) -> int:
    client = resolve_client(args)
    data = client.health()
    rows = [{"status": "ok", "host": client.host, "visibleResults": len(data.get("data", []))}]
    emit(
        args,
        {"status": "ok", "host": client.host, "response": data},
        rows=rows,
        columns=["status", "host", "visibleResults"],
    )
    return 0


def cmd_whoami(args: argparse.Namespace) -> int:
    client = resolve_client(args)
    profile = get_profile(args.profile)
    claims = decode_token(profile.token)
    subject = claims.get("sub")
    result: dict[str, Any] = {
        "token": {
            "sub": subject,
            "email": claims.get("email"),
            "roles": claims.get("roles", []),
            "isBot": claims.get("isBot"),
            "tokenType": claims.get("tokenType"),
            "expiresAt": format_expiry(claims.get("exp")),
        }
    }
    if subject:
        try:
            result["user"] = client.get_user_by_name(
                subject, fields="teams,roles,personas,domains", include="all"
            )
        except OpenMetadataError as exc:
            result["userLookupError"] = str(exc)
    row = {
        "subject": subject or "",
        "email": claims.get("email", ""),
        "tokenType": claims.get("tokenType", ""),
        "isBot": claims.get("isBot", ""),
        "expiresAt": format_expiry(claims.get("exp")),
    }
    emit(
        args,
        result,
        rows=[row],
        columns=["subject", "email", "tokenType", "isBot", "expiresAt"],
    )
    return 0


def cmd_search(args: argparse.Namespace) -> int:
    client = resolve_client(args)
    data = client.search(
        **{
            "q": args.query,
            "index": args.index,
            "from": args.offset,
            "size": args.size,
            "sortField": args.sort_field,
            "sortOrder": args.sort_order,
            "includeSourceFields": args.include_source_fields,
        }
    )
    hits = data.get("hits", {}).get("hits", [])
    rows = []
    for hit in hits:
        source = hit.get("_source", {})
        rows.append(
            {
                "entityType": source.get("entityType", ""),
                "name": source.get("fullyQualifiedName") or source.get("name", ""),
                "score": hit.get("_score", ""),
                "index": hit.get("_index", ""),
            }
        )
    emit(args, data, rows=rows, columns=["entityType", "name", "score", "index"])
    return 0


def cmd_entity_list(args: argparse.Namespace) -> int:
    client = resolve_client(args)
    params = parse_key_values(args.filter)
    params.update({"limit": args.limit, "fields": args.fields, "include": args.include})
    data = client.list_entities(ENTITY_MAP[args.kind], **params)
    rows = []
    for item in data.get("data", []):
        rows.append(
            {
                "name": item.get("fullyQualifiedName") or item.get("name", ""),
                "displayName": item.get("displayName", ""),
                "id": item.get("id", ""),
                "type": item.get("entityType", args.kind.rstrip("s")),
            }
        )
    emit(args, data, rows=rows, columns=["type", "name", "displayName", "id"])
    return 0


def cmd_entity_get(args: argparse.Namespace) -> int:
    client = resolve_client(args)
    data = client.get_entity_by_name(
        ENTITY_MAP[args.kind],
        args.name,
        fields=args.fields,
        include=args.include,
    )
    emit(args, data)
    return 0


def cmd_table_list(args: argparse.Namespace) -> int:
    client = resolve_client(args)
    data = client.list_entities(
        "/tables",
        limit=args.limit,
        database=args.database,
        databaseSchema=args.database_schema,
        fields=args.fields,
        include=args.include,
    )
    rows = []
    for item in data.get("data", []):
        rows.append(
            {
                "name": item.get("fullyQualifiedName", ""),
                "serviceType": item.get("serviceType", ""),
                "tableType": item.get("tableType", ""),
            }
        )
    emit(args, data, rows=rows, columns=["name", "serviceType", "tableType"])
    return 0


def cmd_table_get(args: argparse.Namespace) -> int:
    client = resolve_client(args)
    data = client.get_entity_by_name(
        "/tables",
        args.name,
        fields=args.fields,
        include=args.include,
    )
    emit(args, data)
    return 0


def cmd_raw(args: argparse.Namespace) -> int:
    client = resolve_client(args)
    params = parse_key_values(args.param)
    data = client.raw(args.method, args.path, **params)
    emit(args, data)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except (ValueError, OpenMetadataError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("Interrupted.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
