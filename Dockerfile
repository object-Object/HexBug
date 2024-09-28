FROM ghcr.io/astral-sh/uv:0.4.17 AS uv

FROM python:3.11.10-slim

COPY --from=uv /uv /usr/bin/uv

WORKDIR /app/bot

COPY vendor/ vendor/
COPY pyproject.toml ./
COPY src/HexBug/__init__.py src/HexBug/

RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --system -e '.[runtime]' --find-links ./vendor

COPY .git/ .git/
COPY scripts/bot/ scripts/bot/
COPY src/HexBug/ src/HexBug/
COPY main.py ./

CMD ["python", "main.py"]

HEALTHCHECK \
    --interval=15m \
    --timeout=30s \
    --start-period=2m \
    --start-interval=1m \
    --retries=1 \
    CMD ["python", "scripts/bot/health_check.py"]
