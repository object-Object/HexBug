# used for my vscode extension
import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import TypedDict

from aiohttp import ClientSession
from HexBug.hexdecode.buildpatterns import build_registry
from HexBug.hexdecode.registry import SpecialHandlerPatternInfo
from tqdm import tqdm


class ExtensionPatternInfo(TypedDict):
    name: str
    modid: str
    modName: str
    direction: str | None
    pattern: str | None
    isPerWorld: bool
    args: str | None
    url: str | None
    description: str | None


# don't use this in production
async def _build_registry():
    async with ClientSession() as session:
        return await build_registry(session)


# also don't use this in production
if (registry := asyncio.run(_build_registry())) is None:
    logging.critical("Failed to build registry, exiting.")
    sys.exit(1)

out_dir = Path("out")

out_dir.mkdir(parents=True, exist_ok=True)

output: dict[str, ExtensionPatternInfo] = {}  # translation: PatternJSON
for info in tqdm(registry.patterns):
    if info.translation is None:
        continue

    direction = None
    if not isinstance(info, SpecialHandlerPatternInfo):
        direction = info.direction.name

    args = info.args and info.args.replace("**", "").replace("__", "")

    data: ExtensionPatternInfo = {
        "name": info.name,
        "modid": info.mod.value.modid,
        "modName": info.mod.value.name,
        "direction": direction,
        "pattern": info.pattern,
        "isPerWorld": info.is_great,
        "args": args,
        "url": info.mod.value.build_book_url(info.book_url, False, False)
        if info.book_url is not None
        else None,
        "description": info.description,
    }

    output[info.translation] = data


with open(out_dir / "registry.json", "w", encoding="utf-8") as f:
    json.dump(output, f)
