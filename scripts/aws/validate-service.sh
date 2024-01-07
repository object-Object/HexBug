#!/bin/bash
set -euox pipefail

get_ssm_parameter() {
    aws ssm get-parameter --name "$*" --with-decryption | jq --raw-output '.Parameter.Value'
}

cd /var/lib/codedeploy-apps/HexBug

export AWS_SHARED_CREDENTIALS_FILE=/home/object/codedeploy/temporary-credentials
export AWS_REGION=us-east-1

stage="prod"
bot_id="$(get_ssm_parameter /$stage/HexBug/bot-id)"
webhook="$(get_ssm_parameter /$stage/HexBug/health-check-url)"

attempts=3
want_uuid="$(uuidgen)"

for (( i=1; i<=attempts; i++ )); do
    echo "Waiting for startup. ($i/$attempts)"
    sleep 20s

    echo "Sending message. ($i/$attempts)"
    curl -H "Content-Type: application/json" -d "{\"content\":\"<@$bot_id> health_check $want_uuid\"}" "$webhook"
    sleep 2s

    echo "Checking response. ($i/$attempts)"
    if got_uuid=$(<health_check.txt); then
        if [[ "$want_uuid" == "$got_uuid" ]]; then
            echo "Got expected UUID, health OK."
            exit 0
        fi
    fi
done

echo "Failed to get health check response."
exit 1
