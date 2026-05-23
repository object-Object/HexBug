#!/bin/bash
set -euox pipefail

cd "/var/lib/codedeploy-apps/$APPLICATION_NAME"

docker compose down || echo "Warning: Failed to stop application"
