FROM ghcr.io/astral-sh/uv AS uv

FROM python:3.11

COPY --from=uv /uv /usr/bin/uv

WORKDIR /app/bot

COPY vendor/ vendor/
COPY pyproject.toml ./
COPY src/HexBug/__init__.py src/HexBug/

RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --system -e '.[runtime,target-linux]'

COPY .git/ .git/
COPY scripts/bot/ scripts/bot/
COPY src/HexBug/ src/HexBug/
COPY main.py ./

CMD ["python", "main.py"]

HEALTHCHECK \
    --interval=15m \
    --timeout=30s \
    --start-period=30s \
    --start-interval=30s \
    --retries=3 \
    CMD ["python", "scripts/bot/health_check.py"]
