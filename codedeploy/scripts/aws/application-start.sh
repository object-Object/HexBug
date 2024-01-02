#!/bin/bash
set -euo pipefail

run_pm2() {
    sudo su object -c "pm2 --no-color --mini-list $*"
}

cd /var/lib/codedeploy-apps/HexBug

run_pm2 start pm2.config.js
run_pm2 save
