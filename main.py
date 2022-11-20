import asyncio
import logging
import os
from pathlib import Path

import discord
from discord.ext import commands
from dotenv import load_dotenv

from hexdecode.buildpatterns import build_registry
from utils.commands import HexBugBot


async def main():
    load_dotenv(".env")
    token = os.environ.get("TOKEN")
    if not token:
        raise Exception("TOKEN not found in .env")

    discord.utils.setup_logging(level=logging.INFO)  # WHY ISN'T THIS ENABLED BY DEFAULT

    registry = build_registry()
    intents = discord.Intents.default()
    bot = HexBugBot(registry=registry, command_prefix=commands.when_mentioned, intents=intents)

    async with bot:
        for path in Path("cogs").rglob("*.py"):
            module = ".".join(path.with_name(path.stem).parts)
            logging.log(logging.INFO, f"loading {module}")
            await bot.load_extension(module)
        await bot.start(token)


if __name__ == "__main__":
    asyncio.run(main())
