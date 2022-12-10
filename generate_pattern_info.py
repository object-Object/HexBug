# used for my vscode extension
import json
from typing import TypedDict

from hexdecode.buildpatterns import build_registry
from utils.generate_image import Palette, Theme, generate_image
from utils.mods import ModName
from utils.urls import build_book_url


class PatternInfo(TypedDict):
    name: str
    modName: ModName
    filename: str | None
    direction: str | None
    pattern: str | None
    args: str | None
    url: str | None


registry = build_registry()
output: dict[str, PatternInfo] = {}  # translation: PatternJSON
for name, translation in registry.name_to_translation.items():
    filename = name.replace("/", "_") + ".png" if name not in ["mask", "number"] else None

    direction, pattern, is_great = None, None, None
    if values := registry.translation_to_pattern.get(translation):
        direction, pattern, is_great, _ = values

        if filename is not None:
            for theme in Theme:
                image = generate_image(
                    direction=direction,
                    pattern=pattern,
                    is_great=is_great,
                    palette=Palette.Classic,
                    theme=theme,
                    line_scale=10,
                    arrow_scale=2,
                )
                with open(f"out/patterns/{theme.name.lower()}/{filename}", "wb") as f:
                    f.write(image.getbuffer())

    mod, url = registry.name_to_url.get(name, (None, None))
    if mod is None:  # invalid pattern
        continue

    if args := registry.name_to_args.get(name):
        args = args.replace("**", "").replace("__", "")

    output[translation] = {
        "name": name,
        "modName": mod,
        "filename": filename,
        "direction": direction.name if direction is not None else None,
        "pattern": pattern,
        "args": args,
        "url": build_book_url(mod, url, False, False) if url is not None else None,
    }


with open("out/registry.json", "w", encoding="utf-8") as f:
    json.dump(output, f)
