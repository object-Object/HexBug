#!/bin/bash
set -euox pipefail

cd "/var/lib/codedeploy-apps/$APPLICATION_NAME"

echo -e "\nDEPLOYMENT_TIMESTAMP=\"$(date +%s)\"" >> .env
