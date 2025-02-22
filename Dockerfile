FROM ghcr.io/astral-sh/uv:0.6.2 AS uv
FROM python:3.13.1-slim

WORKDIR /app

COPY requirements.lock ./

# comment out editable requirements, since they're not permitted in constraint files
RUN sed -ir 's/^-e /# -e /g' requirements.lock

COPY vendor/ vendor/

COPY common/pyproject.toml common/
COPY common/src/HexBug/common/__version__.py common/src/HexBug/common/
RUN mkdir -p common/src/HexBug/common && touch common/src/HexBug/common/__init__.py

COPY bot/pyproject.toml bot/
RUN mkdir -p bot/src/HexBug && touch bot/src/HexBug/app.py

# https://github.com/astral-sh/uv/blob/main/docs/docker.md
RUN --mount=from=uv,source=/uv,target=/bin/uv \
    --mount=type=cache,target=/root/.cache/uv \
    PYTHONDONTWRITEBYTECODE=1 \
    uv pip install --system \
    --constraint requirements.lock \
    --find-links vendor \
    -e bot -e common

COPY common/ common/
COPY bot/ bot/

# NOTE: this must be a list, otherwise signals (eg. SIGINT) are not forwarded to the bot
CMD ["/bin/bash", "-c", "python -m HexBug.app"]

HEALTHCHECK \
    --interval=15m \
    --timeout=30s \
    --start-period=2m \
    --start-interval=1m \
    --retries=1 \
    CMD ["python", "-m", "HexBug.health_check"]
