import asyncio
import logging
from pathlib import Path
from typing import Annotated, Any, Coroutine

import httpx
from typer import Option, Typer

from HexBug.core.bot import HexBugBot
from HexBug.core.env import HexBugEnv
from HexBug.data.registry import HexBugRegistry
from HexBug.utils.logging import setup_logging

logger = logging.getLogger(__name__)

app = Typer(
    pretty_exceptions_show_locals=False,
)

try:
    import HexBug.web.app

    app.add_typer(HexBug.web.app.app, name="web")
except ImportError:
    pass


@app.command()
def bot(
    registry_path: Path = Path("registry.json"),
    verbose: Annotated[bool, Option("-v", "--verbose")] = False,
):
    async def bot():
        setup_logging(verbose)
        env = HexBugEnv.load()
        registry = HexBugRegistry.load(registry_path)
        async with HexBugBot(env, registry) as bot:
            await bot.load()
            await bot.start(env.token.get_secret_value())

    run_async(bot())


@app.command()
def build(
    output_path: Annotated[Path, Option("-o", "--output-path")] = Path("registry.json"),
    indent: int | None = None,
    verbose: Annotated[bool, Option("-v", "--verbose")] = False,
):
    setup_logging(verbose)
    registry = HexBugRegistry.build()
    logger.info(f"Saving registry to file: {output_path}")
    registry.save(output_path, indent=indent)


@app.command()
def health_check(
    url: Annotated[str, Option("--url", envvar="HEALTH_CHECK_URL")],
    verbose: Annotated[bool, Option("-v", "--verbose")] = False,
):
    setup_logging(verbose)
    logger.info(f"Sending request to health check url: {url}")
    resp = httpx.get(url).raise_for_status()
    logger.info(f"Response: {resp.text}")


def run_async(main: Coroutine[Any, Any, Any]):
    try:
        asyncio.run(main)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    app()
