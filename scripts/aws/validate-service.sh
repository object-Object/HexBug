#!/bin/bash
set -euox pipefail

run_pm2() {
    sudo su object -c "pm2 --no-color --mini-list $*"
}

# give it time to start up
sleep 10s

# unix timestamp in milliseconds when the process was last started
start="$(run_pm2 jlist | jq --exit-status '[.[] | if .name == "HexBug" then .pm2_env.pm_uptime else null end | values][0]')"

# current unix timestamp in milliseconds
end="$(date +%s%3N)"

elapsed="$(( (end - start) / 1000 ))"
if [[ $elapsed -lt 5 ]]; then
    echo "Uptime too low (expected >=5 seconds, got $elapsed)."
    exit 1
fi
