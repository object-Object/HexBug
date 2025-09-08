# HexBug

A Discord bot for Hex Casting.

The `v2` branch is a total rewrite of the bot. Currently WIP.

## Development

### Setup

Install [uv](https://docs.astral.sh/uv/), then run the following commands to set up your dev environment:

```sh
# set up environment
uv run poe setup

# generate database
docker compose up --detach postgres
uv run alembic upgrade head
```

Note: If using Docker with WSL2 on Windows, [networkingMode=mirrored](https://learn.microsoft.com/en-us/windows/wsl/networking#mirrored-mode-networking) seems to make Postgres connections extremely slow.

### Running

Standalone (faster for development):

```sh
docker compose up --detach postgres
uv run hexbug bot
```

In Docker:

```sh
docker compose up --build
```

### Creating database migrations

https://alembic.sqlalchemy.org/en/latest/autogenerate.html

## TODO

- Set up a test job in the build workflow, including `hexbug bot --no-run` and `pytest`.
- Commands:
  - `/book`
  - `/info`
  - `/palette`
  - `/pattern build`
  - `/patterns hex`
  - `/patterns smart_number`
