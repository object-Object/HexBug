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
    base_dist_path: Annotated[Path, Option("--dist-path")] = Path("dist"),
    base_registry_path: Annotated[Path, Option("--registry-path")] = Path(
        "registry.json"
    ),
    base_web_path: Annotated[Path, Option("--web-path")] = Path("web"),
    indent: int = 4,
    verbose: Annotated[bool, Option("-v", "--verbose")] = False,
):
    setup_logging(verbose)

    logger.info(f"Generating hexdoc props: {output_path}")

    dist_path = base_dist_path.relative_to(output_path.parent, walk_up=True).as_posix()
    registry_path = base_registry_path.relative_to(
        output_path.parent, walk_up=True
    ).as_posix()
    web_path = base_web_path.relative_to(output_path.parent, walk_up=True).as_posix()

    props = HEXDOC_PROPS | {
        "modid": "bookofhexxy",
        "resource_dirs": [
            f"{web_path}/resources",
            *HEXDOC_PROPS["resource_dirs"],
        ],
        "textures": {
            **HEXDOC_PROPS["textures"],
            "enabled": False,
        },
        "template": {
            "icon": f"{web_path}/icon.png",
            "include": [
                "bookofhexxy",
                *(mod.id for mod in MODS),
                "hexdoc",
            ],
            "args": {
                "mod_name": "Book of Hexxy",
                "author": "object-Object",
                "show_landing_text": True,
                "navbar": {
                    "center": [
                        {
                            "text": "registry.json",
                            "href": "../registry/registry.json",
                        },
                        {
                            "text": "GitHub",
                            "href": {"variable": "source_url"},
                        },
                    ],
                },
            },
        },
        "lang": {
            "ru_ru": {"quiet": True},
            "zh_cn": {"quiet": True},
        },
        "extra": {
            "bookofhexxy": {
                "dist_path": dist_path,
                "registry_path": registry_path,
            },
            "hexcasting": {"pattern_stubs": []},
        },
    }

    with output_path.open("wb") as f:
        tomli_w.dump(props, f, indent=indent)
