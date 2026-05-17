# HexBug

A Discord bot for Hex Casting.

If you're here to get your mod added to HexBug, please start by [opening an issue](https://github.com/object-Object/HexBug/issues/new?template=addon-support.yml) using the "Addon support" template.

## Development

### Setup

Install [uv](https://docs.astral.sh/uv/) and clone this repository, then run the following commands in this repository to set up your dev environment:

```sh
# set up environment
uv run poe setup

# generate database
docker compose up --detach postgres
uv run alembic upgrade head
```

Note: If using Docker with WSL2 on Windows, [networkingMode=mirrored](https://learn.microsoft.com/en-us/windows/wsl/networking#mirrored-mode-networking) seems to make Postgres connections extremely slow.

Bot setup (https://discord.com/developers/applications):

- Overview:
  - OAuth2:
    - Redirect: `https://127.0.0.1`
- Activities:
  - Settings:
    - Enable Activities
    - Enable all supported platforms
    - Set maximum participants to 1
  - URL Mappings:
    - Root Mapping: your [Tailscale Funnel](https://tailscale.com/docs/features/tailscale-funnel) URL

### Running

Create a file called `.env`, and fill in your values for `TOKEN`, `CLIENT_SECRET`, and `VITE_CLIENT_ID`:

```sh
# bot
ENVIRONMENT="dev"
TOKEN="discord bot token"
CLIENT_ID="discord bot oauth2 client id"
CLIENT_SECRET="discord bot oauth2 client secret"
API_PORT="6502"
API_ROOT_PATH=""
METRICS_PORT="6500"

# book
GITHUB_REPOSITORY="object-Object/HexBug"
GITHUB_SHA="main"
GITHUB_PAGES_URL="https://book.hexxy.media"

# activity
VITE_CLIENT_ID="discord bot oauth2 client id"
```

Run the bot standalone (faster for development):

```sh
docker compose up --detach postgres
uv run hexbug build --indent 2
uv run hexbug bot
```

Run the bot in Docker:

```sh
docker compose up --build
```

After running the bot for the first time or modifying a command, you'll need to sync slash commands and/or bot emoji. To do this, use the `sync` message command. For example: `@HexBug sync`

Build and serve the Book of Hexxy:

```sh
uv run hexbug build
uv run poe build-data
uv run hexbug web build-props
uv run hexdoc serve
```

### Creating database migrations

https://alembic.sqlalchemy.org/en/latest/autogenerate.html

### Book of Hexxy for addon developers

Gist by penguinencounter: https://gist.github.com/penguinencounter/ace5c45455ea968738a80b8c5e777235

Note that the hexdoc dependencies and static data files have moved from `bot/` to `data/`.
