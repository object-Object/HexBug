import asyncio
import fileinput
import logging
import sys

from aiohttp import ClientSession
from HexBug.hexdecode import revealparser
from HexBug.hexdecode.buildpatterns import build_registry
from HexBug.hexdecode.pretty_print import IotaPrinter


# don't use this in production
async def _build_registry():
    async with ClientSession() as session:
        return await build_registry(session)


# also don't use this in production
if (registry := asyncio.run(_build_registry())) is None:
    logging.critical("Failed to build registry, exiting.")
    sys.exit(1)

printer = IotaPrinter(registry)

for line in fileinput.input(files=[], encoding="utf-8"):
    level = 0
    iota = revealparser.parse(line)
    print(printer.pretty_print(iota))
