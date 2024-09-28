#!/bin/bash
set -euox pipefail

cd /var/lib/codedeploy-apps/HexBug

if ! docker compose exec \
    --env HEALTH_CHECK_DISPLAY_NAME=CodeDeploy \
    --env HEALTH_CHECK_PORT=40405 \
    --env HEALTH_CHECK_STARTUP_DELAY=60 \
    --env HEALTH_CHECK_ATTEMPTS=3 \
    --env HEALTH_CHECK_INTERVAL=30 \
    bot \
    python scripts/bot/health_check.py \
; then
    docker compose logs
    exit 1
fi
