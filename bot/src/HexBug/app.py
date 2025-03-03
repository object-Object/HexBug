import asyncio
from typing import Annotated, Any, Coroutine

from typer import Option, Typer

from HexBug.core.bot import HexBugBot
from HexBug.core.env import HexBugEnv
from HexBug.data.registry import HexBugRegistry
from HexBug.utils.logging import setup_logging

app = Typer(
    pretty_exceptions_show_locals=False,
)


@app.command()
def bot(
    verbose: Annotated[bool, Option("-v", "--verbose")] = False,
):
    async def bot():
        setup_logging(verbose)
        env = HexBugEnv.load()
        async with HexBugBot(env) as bot:
            await bot.load()
            await bot.start(env.token.get_secret_value())

    run_async(bot())


@app.command()
def build(
    verbose: Annotated[bool, Option("-v", "--verbose")] = False,
):
    setup_logging(verbose)
    # TODO: implement
    print(HexBugRegistry.build())


def run_async(main: Coroutine[Any, Any, Any]):
    try:
        asyncio.run(main)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    app()
