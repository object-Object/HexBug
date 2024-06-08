#!/bin/bash
set -euox pipefail

cd /var/lib/codedeploy-apps/HexBug

echo -e "\nDEPLOYMENT_TIMESTAMP=\"$(date +%s)\"" >> .env
