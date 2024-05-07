import logging
import os
import time
import uuid
from pathlib import Path

import boto3
import requests
from mypy_boto3_ssm import SSMClient

HEALTH_CHECK_FILE = Path("data/health_check.txt")

logger = logging.getLogger(__name__)


def main():
    logging.basicConfig()

    ssm: SSMClient = boto3.client(
        "ssm",
        region_name="us-east-1",
    )

    environment = getenv("ENVIRONMENT")
    bot_id = get_parameter(ssm, f"/{environment}/HexBug/bot-id")
    webhook_url = get_parameter(ssm, f"/{environment}/HexBug/health-check-url")

    want_uuid = str(uuid.uuid4())

    logger.info(f"Sending message with UUID: {want_uuid}")

    requests.post(
        webhook_url,
        data={
            "content": f"<@{bot_id}> health_check {want_uuid}",
        },
    ).raise_for_status()

    time.sleep(2)

    logger.info("Checking response.")

    got_uuid = HEALTH_CHECK_FILE.read_text("utf-8")
    if got_uuid != want_uuid:
        raise RuntimeError(f"Incorrect UUID: expected {want_uuid}, got {got_uuid}")

    logger.info("Got expected UUID, health OK.")


def getenv(key: str):
    result = os.getenv(key)
    if not result:
        raise RuntimeError(f"Environment variable not set: {key}")
    return result


def get_parameter(ssm: SSMClient, name: str):
    result = ssm.get_parameter(Name=name, WithDecryption=True)
    if "Value" not in result["Parameter"]:
        raise RuntimeError(f"Failed to get value for parameter: {name}")
    return result["Parameter"]["Value"]


if __name__ == "__main__":
    main()
