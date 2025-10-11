# HexBug

A Discord bot for Hex Casting.

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

Create a file called `.env`:

```sh
# bot
ENVIRONMENT="dev"
TOKEN="put your discord bot token here"
API_PORT="5000"
API_ROOT_PATH=""

# book
GITHUB_REPOSITORY="object-Object/HexBug"
GITHUB_SHA="v2"
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
uv run hexbug web build-props
uv run hexdoc serve
```

### Creating database migrations

https://alembic.sqlalchemy.org/en/latest/autogenerate.html

### Book of Hexxy for addon developers

Gist by penguinencounter: https://gist.github.com/penguinencounter/ace5c45455ea968738a80b8c5e777235
