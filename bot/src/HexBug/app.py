import asyncio
import logging
import sys
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
    run: bool = True,  # disable for CI checks
    verbose: Annotated[bool, Option("-v", "--verbose")] = False,
):
    async def bot() -> int:
        setup_logging(verbose)

        if run:
            env = HexBugEnv.load()
        else:
            env = HexBugEnv.empty()

        registry = HexBugRegistry.load(registry_path)

        async with HexBugBot(env, registry, run) as bot:
            await bot.load()
            if run:
                await bot.start(env.token.get_secret_value())
            elif bot.failed_translations:
                logger.error(
                    f"Failed to validate locale{
                        '' if len(bot.failed_translations) == 1 else 's'
                    }: {
                        ', '.join(
                            sorted(locale.value for locale in bot.failed_translations)
                        )
                    }"
                )
                # calling sys.exit here produces a ton of unnecessary log output
                return 1

        return 0

    sys.exit(run_async(bot()))


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


def run_async[R](main: Coroutine[Any, Any, R]) -> R | None:
    try:
        return asyncio.run(main)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    app()
