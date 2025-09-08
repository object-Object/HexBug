#!/bin/bash
set -euox pipefail

cd "/var/lib/codedeploy-apps/$APPLICATION_NAME"

# start database only
if ! docker compose up --detach --wait --wait-timeout 60 postgres ; then
    docker compose logs
    exit 1
fi

# save the current database revision
# we run this in the bot container because the database does not have ports open in production
alembic_current=$(docker compose run --rm bot alembic current | awk '{print $1}')
echo "Current Alembic revision: ${alembic_current:=base}"

# upgrade the database
docker compose run --rm bot alembic upgrade head

# start the bot
if ! docker compose up --detach --wait --wait-timeout 120 ; then
    docker compose logs

    # roll back the database to the saved revision
    echo "Failed to start bot, rolling back upgrade."
    docker compose run --rm bot alembic downgrade "$alembic_current"

    # stop the database
    docker compose down

    exit 1
fi
