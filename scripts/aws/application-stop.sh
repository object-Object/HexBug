#!/bin/bash
set -euox pipefail

run_pm2() {
    sudo su object -c "pm2 --no-color --mini-list $*"
}

cd /var/lib/codedeploy-apps/HexBug

run_pm2 delete pm2.config.js || true
run_pm2 save
