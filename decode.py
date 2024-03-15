import asyncio
import fileinput
import logging
import sys

from aiohttp import ClientSession
from HexBug.hexdecode import revealparser
from HexBug.hexdecode.buildpatterns import build_registry
from HexBug.hexdecode.hexast import massage_raw_parsed_iota


# don't use this in production
async def _build_registry():
    async with ClientSession() as session:
        return await build_registry(session)


# also don't use this in production
if (registry := asyncio.run(_build_registry())) is None:
    logging.critical("Failed to build registry, exiting.")
    sys.exit(1)

for line in fileinput.input(files=[], encoding="utf-8"):
    level = 0
    iota = revealparser.parse_reveal(line)
    for child in massage_raw_parsed_iota(iota, registry):
        level = child.preadjust(level)
        print(child.print(level, True, registry))
        level = child.postadjust(level)
