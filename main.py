import asyncio
import logging
import os
import sys
from pathlib import Path

import discord
from aiohttp import ClientSession
from discord.ext import commands
from dotenv import load_dotenv

from hexdecode.buildpatterns import build_registry
from utils.commands import HexBugBot


async def main():
    # load environment variables
    load_dotenv(".env")
    token = os.environ.get("TOKEN")
    if not token:
        raise Exception("TOKEN not found in .env")

    # set up logging
    discord.utils.setup_logging(level=logging.INFO)  # WHY ISN'T THIS ENABLED BY DEFAULT
    discord.VoiceClient.warn_nacl = False

    # build registry, hopefully
    async with ClientSession() as session:
        if (registry := await build_registry(session)) is None:
            logging.critical("Failed to build registry, exiting.")
            sys.exit(1)

    intents = discord.Intents.default()
    bot = HexBugBot(registry=registry, command_prefix=commands.when_mentioned, intents=intents)

    # load modules and run the bot
    async with bot:
        for path in Path("cogs").rglob("*.py"):
            module = ".".join(path.with_name(path.stem).parts)

            logging.info(f"loading {module}")
            await bot.load_extension(module)

        await bot.start(token)


if __name__ == "__main__":
    asyncio.run(main())
