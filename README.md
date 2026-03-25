# openmetadata-cli

Minimal command-line client for OpenMetadata with local profile storage and Arch Linux packaging.

## Features

- Token-based login against an OpenMetadata instance
- Persist profiles under `~/.config/openmetadata-cli/config.json`
- Verify connectivity and credentials
- Inspect the authenticated principal
- Search entities
- List and retrieve common entities such as tables and users
- Raw API passthrough for unsupported endpoints

## Install for development

```bash
python -m build
python -m installer --destdir /tmp/openmetadata-cli-dist dist/*.whl
python -m pip install --user .
```

## Quick start

```bash
omctl login --profile work --host https://openmetadata.example.com --token '...'
omctl auth status
omctl whoami
omctl search customer --index table_search_index
omctl table get sample_data.ecommerce_db.shopify.dim_address --fields columns,owners,tags
```

## Credentials

OpenMetadata API access uses JWT bearer tokens.

- Bot token: recommended for automation
- Personal access token: suitable for user-driven CLI usage

You do not log in with username and password through the API. You generate a JWT in the OpenMetadata UI and store that token locally with `omctl login`.

The CLI stores the token in `~/.config/openmetadata-cli/config.json` with mode `0600`.

## Pacman packaging

Build the package with:

```bash
makepkg -si
```

This installs the `omctl` executable.
