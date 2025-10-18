FROM ghcr.io/astral-sh/uv:0.6.2 AS uv
FROM python:3.12.9-slim

ENV UV_PROJECT_ENVIRONMENT=/usr/local
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

WORKDIR /app

# dependencies

COPY vendor/ vendor/
COPY pyproject.toml ./
COPY uv.lock ./

RUN --mount=from=uv,source=/uv,target=/bin/uv \
    --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-default-groups --package HexBug-bot --no-install-workspace

# project code

COPY common/ common/
COPY bot/ bot/
COPY CHANGELOG.md bot/src/HexBug/resources/

# sync dependencies with data to build registry

RUN --mount=from=uv,source=/uv,target=/bin/uv \
    --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-default-groups --package HexBug-bot --extra data

RUN hexbug build

# sync dependencies without data to reduce image size hopefully idk i didn't check

RUN --mount=from=uv,source=/uv,target=/bin/uv \
    --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-default-groups --package HexBug-bot

# Alembic files

COPY alembic/ alembic/
COPY alembic.ini ./

# NOTE: this must be a list, otherwise signals (eg. SIGINT) are not forwarded to the bot
CMD ["hexbug", "bot"]

HEALTHCHECK \
    --interval=1m \
    --timeout=30s \
    --start-period=2m \
    --start-interval=15s \
    --retries=3 \
    CMD ["hexbug", "health-check"]
