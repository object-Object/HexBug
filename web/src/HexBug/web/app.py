import logging
from pathlib import Path
from typing import Annotated

import tomli_w
from typer import Option, Typer

from HexBug.data.static_data import HEXDOC_PROPS, MODS
from HexBug.utils.logging import setup_logging

logger = logging.getLogger(__name__)

app = Typer(
    pretty_exceptions_show_locals=False,
)


@app.command()
def build_props(
    output_path: Annotated[Path, Option("-o", "--output-path")] = Path("hexdoc.toml"),
    registry_path: Annotated[Path, Option("--registry-path")] = Path("registry.json"),
    web_path: Annotated[Path, Option("--web-path")] = Path("web"),
    indent: int = 4,
    verbose: Annotated[bool, Option("-v", "--verbose")] = False,
):
    setup_logging(verbose)

    logger.info(f"Generating hexdoc props: {output_path}")

    registry = registry_path.relative_to(output_path.parent, walk_up=True).as_posix()
    web = web_path.relative_to(output_path.parent, walk_up=True).as_posix()

    props = HEXDOC_PROPS | {
        "modid": "bookofhexxy",
        "resource_dirs": [
            f"{web}/resources",
            *HEXDOC_PROPS["resource_dirs"],
        ],
        "textures": {
            **HEXDOC_PROPS["textures"],
            "enabled": False,
        },
        "template": {
            "icon": f"{web}/icon.png",
            "include": [
                "bookofhexxy",
                *(mod.id for mod in MODS),
                "hexdoc",
            ],
            "args": {
                "mod_name": "Book of Hexxy",
                "author": "object-Object",
                "show_landing_text": True,
            },
        },
        "lang": {
            "ru_ru": {"quiet": True},
            "zh_cn": {"quiet": True},
        },
        "extra": {
            "bookofhexxy": {
                "registry_path": registry,
            },
            "hexcasting": {"pattern_stubs": []},
        },
    }

    with output_path.open("wb") as f:
        tomli_w.dump(props, f, indent=indent)
