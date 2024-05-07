from __future__ import annotations

import logging
import sys
import time
import traceback
import uuid
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, ClassVar

import requests
from pydantic import Field
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


class Env(BaseSettings):
    model_config = {
        "env_prefix": "health_check_",
        "env_file": ".env",
        "extra": "ignore",
    }

    # non-prefixed
    environment: str = Field(alias="environment")
    bot_id: str = Field(alias="bot_id")

    webhook_url: str = Field(repr=False)
    display_name: str

    port: int = Field(ge=1024, le=65535)

    startup_delay: int = Field(ge=0)  # seconds
    timeout: int = Field(ge=1)  # seconds
    attempts: int = Field(ge=1)
    interval: int = Field(ge=0)  # seconds


class HealthCheckServer(HTTPServer):
    def handle_timeout(self) -> None:
        logger.warning(f"Request timed out after {self.timeout} seconds.")


class HealthCheckHandler(BaseHTTPRequestHandler):
    want_uuid: ClassVar[str | None] = None

    def do_GET(self):
        prefix = "/health-check-reply/"
        got_uuid = self.path.removeprefix(prefix)

        if got_uuid == self.path:
            self.send_error(
                400,
                f"Invalid path (expected {prefix}{{uuid}}): {self.path}",
            )
            return

        if got_uuid != self.want_uuid:
            self.send_error(
                400,
                f"Invalid UUID (expected {self.want_uuid}): {got_uuid}",
            )
            return

        self.send_response(200)
        self.end_headers()

        logger.info("Got expected UUID, health OK.")
        sys.exit(0)

    def log_message(self, format: str, *args: Any) -> None:
        logger.info(format, *args)


def send_health_check(env: Env, attempt: int):
    uuid = HealthCheckHandler.want_uuid
    logger.info(f"Sending message with UUID ({attempt}/{env.attempts}): {uuid}")
    requests.post(
        env.webhook_url,
        data=dict(
            username=env.display_name,
            content=f"<@{env.bot_id}> health_check {env.port} {uuid}",
        ),
    ).raise_for_status()


def sleep(seconds: int):
    if seconds:
        logger.info(f"Waiting for {seconds} seconds...")
        time.sleep(seconds)


def main():
    logging.basicConfig(level=logging.INFO)

    env = Env.model_validate({})
    logger.info(f"Env: {env}")

    sleep(env.startup_delay)

    logger.info(f"Starting server on port {env.port}.")
    with HealthCheckServer(("", env.port), HealthCheckHandler) as httpd:
        httpd.timeout = env.timeout

        for i in range(1, env.attempts + 1):
            HealthCheckHandler.want_uuid = str(uuid.uuid4())

            send_health_check(env, i)
            httpd.handle_request()

            if i < env.attempts:
                sleep(env.interval)

    logger.error("Did not receive health check response.")
    sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
