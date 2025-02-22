#!/bin/bash
set -euox pipefail

cd /var/lib/codedeploy-apps/HexBug

docker compose down
