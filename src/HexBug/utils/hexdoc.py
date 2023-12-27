import os
from contextlib import contextmanager
from pathlib import Path

from hexdoc.cli.utils.load import load_book
from hexdoc.core import MinecraftVersion, ModResourceLoader, Properties
from hexdoc.data import HexdocMetadata
from hexdoc.minecraft import I18n
from hexdoc.patchouli import Book
from hexdoc.plugin import PluginManager
from hexdoc_hexcasting.metadata import PatternMetadata


@contextmanager
def load_hexdoc_mod(
    *,
    modid: str,
    book_id: str,
    lang: str = "en_us",
):
    os.environ |= {
        "GITHUB_SHA": "main",
        "GITHUB_REPOSITORY": "object-Object/HexBug",
        "GITHUB_PAGES_URL": "https://object-object.github.io/HexBug",
    }

    props = Properties.load_data(
        props_dir=Path.cwd(),
        data={
            "modid": modid,
            "book": book_id,
            "default_lang": lang,
            "default_branch": "main",
            "resource_dirs": [
                {"modid": modid, "external": False},
                {"modid": "hexcasting"},
                {"modid": "minecraft"},
                {"modid": "hexdoc"},
            ],
            "extra": {"hexcasting": {"pattern_stubs": []}},
            "textures": {
                "missing": [
                    "minecraft:chest",
                    "hexgloop:fake_spellbook_for_rei",
                    "emi:*",
                ]
            },
        },
    )
    assert props.book_id

    pm = PluginManager("", props)
    plugin = pm.mod_plugin(modid, book=True)
    MinecraftVersion.MINECRAFT_VERSION = pm.minecraft_version()

    with ModResourceLoader.load_all(props, pm) as loader:
        all_metadata = loader.load_metadata(model_type=HexdocMetadata)
        hex_metadata = loader.load_metadata(
            name_pattern="{modid}.patterns",
            model_type=PatternMetadata,
            allow_missing=True,
        )[modid]

        book_data = Book.load_book_json(loader, props.book_id)

        i18n = I18n.load(loader, book_data, lang)

        book, context = load_book(
            book_data=book_data,
            pm=pm,
            loader=loader,
            i18n=i18n,
            all_metadata=all_metadata,
        )

        yield plugin, book, context, all_metadata[modid], hex_metadata
