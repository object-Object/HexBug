import logging
import os
from contextlib import contextmanager
from pathlib import Path
from types import ModuleType
from typing import cast

import hexdoc_hexcasting._hooks
from hexdoc.cli.utils.load import init_context
from hexdoc.core import (
    MinecraftVersion,
    ModResourceLoader,
    Properties,
    ResourceLocation,
)
from hexdoc.core.properties import LangProps
from hexdoc.data import HexdocMetadata
from hexdoc.minecraft import I18n
from hexdoc.patchouli.text import FormatTree, Style
from hexdoc.plugin import PluginManager
from hexdoc_hexcasting.metadata import PatternMetadata
from jinja2 import Environment, PackageLoader

from .book_types import Book as BookDict

logger = logging.getLogger("bot")


# lots of things are failing this check, so don't kill the bot when it fails

real_check_action_links = hexdoc_hexcasting._hooks.check_action_links


def _check_action_links(tree: FormatTree, in_link: bool, action_style: Style):
    try:
        real_check_action_links(tree, in_link, action_style)
    except ValueError as e:
        logger.warning(f"{e.__class__.__name__}: {e}")


hexdoc_hexcasting._hooks.check_action_links = _check_action_links


def load_plugin_manager():
    return PluginManager("", cast(Properties, None))  # lie


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
                    "minecraft:shield",
                    "hexgloop:fake_spellbook_for_rei",
                    "emi:*",
                ]
            },
        },
    )
    assert props.book_id

    pm = PluginManager("", props)
    mod_plugin = pm.mod_plugin(modid, book=True)
    book_plugin = pm.book_plugin("patchouli")
    MinecraftVersion.MINECRAFT_VERSION = pm.minecraft_version()

    with ModResourceLoader.load_all(props, pm) as loader:
        all_metadata = loader.load_metadata(model_type=HexdocMetadata)
        hex_metadata = loader.load_metadata(
            name_pattern="{modid}.patterns",
            model_type=PatternMetadata,
            allow_missing=True,
        )[modid]

        real_book_id, book_data = book_plugin.load_book_data(props.book_id, loader)

        i18n = I18n.load(loader, book_plugin.is_i18n_enabled(book_data), lang)

        context = init_context(
            book_id=real_book_id,
            book_data=book_data,
            pm=pm,
            loader=loader,
            i18n=i18n,
            all_metadata=all_metadata,
        )

        book = book_plugin.validate_book(book_data, context=context)

        yield mod_plugin, book, context, all_metadata[modid], hex_metadata


def patch_collate_data(
    collate_data: ModuleType,
    *,
    book_id: ResourceLocation,
    pm: PluginManager,
):
    def _format_string(root_data: BookDict, string: str) -> FormatTree:
        i18n = I18n(
            lookup=I18n.parse_lookup(root_data["i18n"]),
            lang="en_us",
            default_i18n=None,
            enabled=True,
            lang_props=LangProps(quiet=True),
        )
        return FormatTree.format(
            i18n.localize(string).value,
            book_id=book_id,
            i18n=i18n,
            macros=root_data["macros"],
            is_0_black=False,
            pm=pm,
            link_overrides={},
        )

    setattr(collate_data, "format_string", _format_string)


def format_text(text: FormatTree) -> str:
    loader = PackageLoader("hexdoc", "_templates")
    env = Environment(loader=loader)

    # TODO: we *should* be using formatting.md.jinja here
    # but we don't have book_links for collate_data, so link formatting fails :(
    template = env.from_string(
        """\
        {%- import "macros/formatting.txt.jinja" as fmt with context -%}
        {{- fmt.styled(text) -}}
        """
    )
    return template.render(text=text)
