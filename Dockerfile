FROM ghcr.io/astral-sh/uv:0.6.2 AS uv
FROM python:3.12.9-alpine

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
    uv sync --frozen --no-dev --package HexBug-bot --no-install-workspace

# project code

COPY common/ common/
COPY bot/ bot/

RUN --mount=from=uv,source=/uv,target=/bin/uv \
    --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --package HexBug-bot

# NOTE: this must be a list, otherwise signals (eg. SIGINT) are not forwarded to the bot
CMD ["python", "-m", "HexBug.app"]

HEALTHCHECK \
    --interval=15m \
    --timeout=30s \
    --start-period=2m \
    --start-interval=1m \
    --retries=1 \
    CMD ["python", "-m", "HexBug.health_check"]
