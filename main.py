import asyncio
import logging
import os
import sys
from pathlib import Path

import discord
from aiohttp import ClientSession
from discord.ext import commands
from discord.utils import _ColourFormatter
from dotenv import load_dotenv
from HexBug.hexdecode.buildpatterns import build_registry
from HexBug.utils.commands import HexBugBot

MIN_PYTHON = (3, 11)
if sys.version_info < MIN_PYTHON:
    sys.exit(f"Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]} or later is required.")


def _get_env(key: str) -> str:
    value = os.environ.get(key)
    if not value:
        raise Exception(f"{key} not found in .env")
    return value


def _setup_logging():
    # use the default discord.py formatter, it looks nice
    formatter = _ColourFormatter()

    # root logger, only info and up for most things
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # logger for bot messages, allow debug
    logging.getLogger("bot").setLevel(logging.DEBUG)

    # send debug and info to stdout
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(formatter)
    stdout_handler.setLevel(logging.DEBUG)
    stdout_handler.addFilter(lambda r: r.levelno <= logging.INFO)
    logger.addHandler(stdout_handler)

    # send warning, error, and critical to stderr
    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setFormatter(formatter)
    stderr_handler.setLevel(logging.WARNING)
    logger.addHandler(stderr_handler)

    # don't show the "voice won't work" warning
    discord.VoiceClient.warn_nacl = False


async def main():
    # load environment variables
    load_dotenv(".env")
    token = _get_env("TOKEN")
    log_webhook_url = _get_env("LOG_WEBHOOK_URL")
    health_check_channel_id = int(_get_env("HEALTH_CHECK_CHANNEL_ID"))

    _setup_logging()

    # build registry, hopefully
    async with ClientSession() as session:
        if (registry := await build_registry(session)) is None:
            logging.critical("Failed to build registry, exiting.")
            sys.exit(1)

        intents = discord.Intents.default()
        bot = HexBugBot(
            registry=registry,
            session=session,
            log_webhook_url=log_webhook_url,
            health_check_channel_id=health_check_channel_id,
            command_prefix=commands.when_mentioned,
            intents=intents,
        )

        # load modules and run the bot
        async with bot:
            logger = logging.getLogger("bot")
            for path in Path("src/HexBug/cogs").rglob("*.py"):
                if path.stem == "__init__":
                    continue

                module = ".".join(path.with_name(path.stem).parts[1:])
                logger.info(f"Loading {module}")
                await bot.load_extension(module)

            await bot.start(token)


if __name__ == "__main__":
    asyncio.run(main())
