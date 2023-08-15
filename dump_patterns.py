import asyncio
import csv
import logging
import sys
from dataclasses import asdict

from aiohttp import ClientSession

from HexBug.hexdecode.buildpatterns import build_registry
from HexBug.hexdecode.registry import Registry


def _sorted_patterns(registry: Registry):
    return sorted(
        registry.patterns,
        key=lambda p: (p.mod.value.name, p.translation),
    )


# don't use this in production
async def _build_registry():
    async with ClientSession() as session:
        return await build_registry(session)


# also don't use this in production
registry = asyncio.run(_build_registry())
if registry is None:
    logging.critical("Failed to build registry, exiting.")
    sys.exit(1)


columns = [
    "mod",
    "translation",
    "direction",
    "pattern",
    "is_great",
    "modid",
    "name",
    "classname",
    "args",
    "book_anchor",
]


filename = sys.argv[1] if len(sys.argv) > 1 else "patterns.csv"
with open(filename, "w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(
        f,
        columns,
        extrasaction="ignore",
        lineterminator="\n",
    )

    writer.writeheader()
    for pattern in _sorted_patterns(registry):
        writer.writerow(
            asdict(pattern)
            | {
                "mod": pattern.mod.value.name,
                "direction": pattern.direction.name if pattern.direction else None,
                "is_great": str(pattern.is_great).lower(),
                "modid": pattern.mod.value.modid,
                "book_anchor": pattern.book_url,
            }
        )
