# used for my vscode extension
import asyncio
import json
import logging
import sys
from typing import TypedDict

from aiohttp import ClientSession

from HexBug.hexdecode.buildpatterns import build_registry
from HexBug.hexdecode.registry import SpecialHandlerPatternInfo
from HexBug.utils.generate_image import Palette, Theme, draw_single_pattern


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


# don't use this in production
async def _build_registry():
    async with ClientSession() as session:
        return await build_registry(session)


# also don't use this in production
if (registry := asyncio.run(_build_registry())) is None:
    logging.critical("Failed to build registry, exiting.")
    sys.exit(1)

output: dict[str, ExtensionPatternInfo] = {}  # translation: PatternJSON
for info in registry.patterns:
    if info.translation is None:
        continue

    filename, width, height, direction = None, None, None, None

    if not isinstance(info, SpecialHandlerPatternInfo):
        filename = info.name.replace("/", "_") + ".png"
        direction = info.direction.name
        for theme in Theme:
            image, (width, height) = draw_single_pattern(
                direction=info.direction,
                pattern=info.pattern,
                is_great=info.is_great,
                palette=Palette.Classic,
                theme=theme,
                line_scale=6,
                arrow_scale=2,
            )
            with open(f"out/patterns/{theme.name.lower()}/{filename}", "wb") as f:
                f.write(image.getbuffer())

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
        "url": info.mod.value.build_book_url(info.book_url, False, False) if info.book_url is not None else None,
    }

    output[info.translation] = data


with open("out/registry.json", "w", encoding="utf-8") as f:
    json.dump(output, f)
