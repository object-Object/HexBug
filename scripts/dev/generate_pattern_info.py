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
from HexBug.rendering import Palette, Theme, draw_patterns, get_grid_options
from tqdm import tqdm


class ImageInfo(TypedDict):
    filename: str
    height: int
    width: int


class ExtensionPatternInfo(TypedDict):
    name: str
    modid: str
    modName: str
    image: ImageInfo | None
    direction: str | None
    pattern: str | None
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
patterns_dir = out_dir / "patterns"

out_dir.mkdir(parents=True, exist_ok=True)
patterns_dir.mkdir(parents=True, exist_ok=True)
for theme in Theme:
    (patterns_dir / theme.name.lower()).mkdir(parents=True, exist_ok=True)

output: dict[str, ExtensionPatternInfo] = {}  # translation: PatternJSON
for info in tqdm(registry.patterns):
    if info.translation is None:
        continue

    filename, width, height, direction = None, None, None, None

    if not isinstance(info, SpecialHandlerPatternInfo):
        filename = info.name.replace("/", "_") + ".png"
        direction = info.direction.name
        for theme in Theme:
            options = get_grid_options(
                palette=Palette.Classic,
                theme=theme,
                per_world=info.is_great,
            )
            image = draw_patterns((info.direction, info.pattern), options)
            width, height = image.size
            image.save(patterns_dir / theme.name.lower() / filename)

    args = info.args and info.args.replace("**", "").replace("__", "")

    data: ExtensionPatternInfo = {
        "name": info.name,
        "modid": info.mod.value.modid,
        "modName": info.mod.value.name,
        "image": {
            "filename": filename,
            "height": height,
            "width": width,
        }
        if filename and height and width
        else None,
        "direction": direction,
        "pattern": info.pattern,
        "args": args,
        "url": info.mod.value.build_book_url(info.book_url, False, False)
        if info.book_url is not None
        else None,
        "description": info.description,
    }

    output[info.translation] = data


with open(out_dir / "registry.json", "w", encoding="utf-8") as f:
    json.dump(output, f)
