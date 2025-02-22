#!/bin/bash
set -euox pipefail

cd /var/lib/codedeploy-apps/HexBug

docker login ghcr.io --username object-Object --password-stdin < /var/lib/codedeploy-apps/.cr_pat

if ! docker compose up --detach ; then
    docker compose logs
    exit 1
fi
