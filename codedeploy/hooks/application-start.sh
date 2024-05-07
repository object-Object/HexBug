#!/bin/bash
set -euox pipefail

cd /var/lib/codedeploy-apps/HexBug

# shellcheck disable=SC1091
source image_version

if ! docker compose up --detach --wait --wait-timeout 120 ; then
    docker compose logs
    docker inspect --format "{{json .State.Health}}" hexbug-bot-1 | jq '.Log[].Output'
    exit 1
fi
