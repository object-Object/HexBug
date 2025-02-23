import asyncio

from HexBug.core.env import HexBugEnv
from HexBug.discord.bot import HexBugBot
from HexBug.utils.logging import setup_logging


async def main():
    setup_logging()
    env = HexBugEnv.load()
    async with HexBugBot(env) as bot:
        await bot.load()
        await bot.start(env.token.get_secret_value())


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
