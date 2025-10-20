import asyncio
import code
import logging
import platform
import sys
import textwrap
from pathlib import Path
from typing import Annotated, Any, Coroutine

import httpx
from discord import Locale
from hexdoc.utils.logging import repl_readfunc
from pydantic import TypeAdapter
from typer import Option, Typer

from HexBug.core.bot import HexBugBot
from HexBug.core.env import HexBugEnv
from HexBug.data.hex_math import HexDir, HexPattern, PatternSignature
from HexBug.data.parsers import load_parsers
from HexBug.data.registry import HexBugRegistry
from HexBug.resources import load_resource
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

        # do this after logging is set up so we see any warnings from lark
        load_parsers()

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
                # fail if en-US has errors, else just log the error message and continue
                # calling sys.exit here produces a ton of unnecessary log output
                return 1 if Locale.american_english in bot.failed_translations else 0

        return 0

    sys.exit(run_async(bot()))


@app.command()
def build(
    output_path: Annotated[Path, Option("-o", "--output-path")] = Path("registry.json"),
    indent: int | None = None,
    verbose: Annotated[bool, Option("-v", "--verbose")] = False,
):
    setup_logging(verbose)

    ta = TypeAdapter(dict[int, tuple[HexDir, PatternSignature]])
    data = ta.validate_json(load_resource("numbers_2000.json"))
    pregenerated_numbers = {
        n: HexPattern(direction, signature)
        for n, (direction, signature) in data.items()
    }

    registry = HexBugRegistry.build(pregenerated_numbers=pregenerated_numbers)
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
    # https://www.psycopg.org/psycopg3/docs/advanced/async.html#async
    if platform.system() == "Windows":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    try:
        return asyncio.run(main)
    except KeyboardInterrupt:
        pass


@app.command()
def repl(
    registry_path: Path = Path("registry.json"),
    verbose: Annotated[bool, Option("-v", "--verbose")] = False,
):
    setup_logging(verbose)

    registry = HexBugRegistry.load(registry_path)

    repl_locals = dict[str, Any](
        registry=registry,
        mods=registry.mods,
        patterns=registry.patterns,
        special_handlers=registry.special_handlers,
        lookups=registry.lookups,
    )

    code.interact(
        banner=textwrap.dedent(
            f"""\
            [HexBug repl] Python {sys.version}
            Locals: {", ".join(sorted(repl_locals.keys()))}"""
        ),
        readfunc=repl_readfunc(),
        local=repl_locals,
        exitmsg="",
    )


if __name__ == "__main__":
    app()
