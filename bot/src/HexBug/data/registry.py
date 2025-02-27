import logging
import os
from pathlib import Path
from typing import Self

from hexdoc.cli.utils import init_context
from hexdoc.core import MinecraftVersion, ModResourceLoader, Properties
from hexdoc.data import HexdocMetadata
from hexdoc.minecraft import I18n
from hexdoc.patchouli import Book
from hexdoc.plugin import PluginManager
from pydantic import BaseModel

from .mods import STATIC_MOD_INFO, DynamicModInfo, ModInfo

logger = logging.getLogger(__name__)


class HexBugRegistry(BaseModel):
    mods: list[ModInfo]

    @classmethod
    def build(cls) -> Self:
        # lazy import because hexdoc_hexcasting won't be available when the bot runs
        from hexdoc_hexcasting.metadata import PatternMetadata

        for key in ["GITHUB_SHA", "GITHUB_REPOSITORY", "GITHUB_PAGES_URL"]:
            os.environ.setdefault(key, "")

        logger.info("Initializing hexdoc")

        props = Properties.load_data(
            props_dir=Path.cwd(),
            data={
                "modid": "hexcasting",
                "book": "hexcasting:thehexbook",
                "resource_dirs": [
                    *({"modid": mod.id, "external": False} for mod in STATIC_MOD_INFO),
                    {"modid": "minecraft"},
                    {"modid": "hexdoc"},
                ],
                "extra": {"hexcasting": {"pattern_stubs": []}},
                "textures": {
                    "missing": [
                        "minecraft:chest",
                        "minecraft:shield",
                        "emi:*",
                    ]
                },
            },
        )
        assert props.book_id

        pm = PluginManager("", props)
        MinecraftVersion.MINECRAFT_VERSION = pm.minecraft_version()
        book_plugin = pm.book_plugin("patchouli")

        logger.info("Loading resources")

        with ModResourceLoader.load_all(props, pm, export=False) as loader:
            logger.info("Loading metadata")

            hexdoc_metadatas = loader.load_metadata(model_type=HexdocMetadata)
            pattern_metadatas = loader.load_metadata(
                name_pattern="{modid}.patterns",
                model_type=PatternMetadata,
                allow_missing=True,
            )

            logger.info("Loading i18n")

            i18n = I18n.load(loader, enabled=True, lang="en_us")

            logger.info("Loading book")

            book_id, book_data = book_plugin.load_book_data(props.book_id, loader)
            context = init_context(
                book_id=book_id,
                book_data=book_data,
                pm=pm,
                loader=loader,
                i18n=i18n,
                all_metadata=hexdoc_metadatas,
            )
            book = book_plugin.validate_book(book_data, context=context)
            assert isinstance(book, Book)

            mods = list[ModInfo]()

            for mod in STATIC_MOD_INFO:
                logger.info(f"Loading mod: {mod.id}")

                mod_plugin = pm.mod_plugin(mod.id, book=True)
                hexdoc_metadata = hexdoc_metadatas[mod.id]
                pattern_metadata = pattern_metadatas[mod.id]

                if hexdoc_metadata.book_url is None:
                    raise ValueError(f"Mod missing book url: {mod.id}")

                _, author, repo, commit = hexdoc_metadata.asset_url.parts

                mods.append(
                    ModInfo.from_parts(
                        mod,
                        DynamicModInfo(
                            version=mod_plugin.mod_version,
                            book_url=hexdoc_metadata.book_url,
                            github_author=author,
                            github_repo=repo,
                            github_commit=commit,
                        ),
                    )
                )

        return cls(mods=mods)

    @classmethod
    def load(cls, path: Path) -> Self:
        data = path.read_text(encoding="utf-8")
        return cls.model_validate_json(data)

    def save(self, path: Path):
        data = self.model_dump_json(round_trip=True)
        path.write_text(data, encoding="utf-8")
