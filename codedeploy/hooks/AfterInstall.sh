#!/bin/bash
set -euox pipefail

cd "/var/lib/codedeploy-apps/$APPLICATION_NAME"

echo -e "\nDEPLOYMENT__TIMESTAMP=\"$(date +%s)\"" >> .env

docker login ghcr.io --username object-Object --password-stdin < /var/lib/codedeploy-apps/.cr_pat

docker compose pull
