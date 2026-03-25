<div align="center">

# open-metadata-cli

[![Release](https://img.shields.io/github/v/release/decent-tools-for-thought/open-metadata-cli?sort=semver&color=0f766e)](https://github.com/decent-tools-for-thought/open-metadata-cli/releases)
![Python](https://img.shields.io/badge/python-3.11%2B-0ea5e9)
![License](https://img.shields.io/badge/license-MIT-14b8a6)

Command-line client for OpenMetadata with saved profiles, token inspection, entity discovery, and raw API access.

</div>

## Map
- [Install](#install)
- [Functionality](#functionality)
- [Authentication](#authentication)
- [Quick Start](#quick-start)
- [Development](#development)
- [Arch Packaging](#arch-packaging)

## Install

```bash
python -m pip install .
omctl --help
```

## Functionality

- `omctl login`: store a host and JWT token in a named local profile.
- `omctl profiles`: list, select, and delete saved profiles.
- `omctl auth status`: verify stored credentials against the OpenMetadata API.
- `omctl whoami`: decode token claims and attempt a matching user lookup.
- `omctl search`: query OpenMetadata search indexes.
- `omctl entity list|get`: generic entity access for common entity types.
- `omctl table list|get`: convenience wrappers for the table entity endpoints.
- `omctl raw`: call an arbitrary OpenMetadata API path for unsupported reads.

## Authentication

OpenMetadata API access uses JWT bearer tokens.

- Bot token: preferred for automation.
- Personal access token: suitable for interactive CLI use.

The CLI does not implement username/password login through the API. Generate a JWT in the OpenMetadata UI and store it locally with `omctl login`.

Profiles are written to `~/.config/openmetadata-cli/config.json` with file mode `0600`.

## Quick Start

```bash
omctl login --profile work --host https://openmetadata.example.com --token '...'
omctl auth status
omctl whoami
omctl search customer --index table_search_index
omctl entity list user --limit 5
omctl table get sample_data.ecommerce_db.shopify.dim_address --fields columns,owners,tags
omctl raw /users --param limit=5
```

## Development

```bash
uv sync --group dev
uv run ruff format .
uv run ruff check .
uv run mypy
uv run pytest
uv build
```

## Arch Packaging

The repository includes a root `PKGBUILD` for local `makepkg` builds and eventual AUR publication.

```bash
sudo pacman -S --needed base-devel python-build python-installer python-setuptools
makepkg -si
```

This installs the `omctl` executable and packages the checked-out source tree directly.
