from __future__ import annotations

import logging
import os
from collections import defaultdict
from itertools import zip_longest
from pathlib import Path
from typing import TYPE_CHECKING, Self

from hexdoc.cli.utils import init_context
from hexdoc.core import (
    MinecraftVersion,
    ModResourceLoader,
    Properties,
    ResourceLocation,
)
from hexdoc.data import HexdocMetadata
from hexdoc.jinja.render import create_jinja_env_with_loader
from hexdoc.minecraft import I18n
from hexdoc.patchouli import Book, BookContext, Entry
from hexdoc.patchouli.page import TextPage
from hexdoc.plugin import PluginManager
from jinja2 import PackageLoader
from pydantic import BaseModel

from HexBug.utils.hexdoc import HexBugBookContext

from .hex_math import HexDir
from .mods import STATIC_MOD_INFO, DynamicModInfo, ModInfo
from .patterns import EXTRA_PATTERNS, PatternInfo, PatternOperator

if TYPE_CHECKING:
    from hexdoc_hexcasting.book.page import (
        ManualOpPatternPage,
        ManualRawPatternPage,
        PageWithOpPattern,
    )

    type PatternPage = PageWithOpPattern | ManualOpPatternPage | ManualRawPatternPage

    type _PatternBookInfo = tuple[Entry, PatternPage, TextPage | None]
    """entry, page, next_page"""


logger = logging.getLogger(__name__)


class HexBugRegistry(BaseModel):
    mods: dict[str, ModInfo]
    patterns: dict[ResourceLocation, PatternInfo]

    @classmethod
    def build(cls) -> Self:
        logger.info("Building HexBug registry.")

        # lazy imports because hexdoc_hexcasting won't be available when the bot runs
        from hexdoc_hexcasting.book.page import (
            ManualOpPatternPage,
            ManualRawPatternPage,
            PageWithOpPattern,
        )
        from hexdoc_hexcasting.metadata import PatternMetadata

        registry = cls(mods={}, patterns={})

        # load hexdoc data

        for key in ["GITHUB_SHA", "GITHUB_REPOSITORY", "GITHUB_PAGES_URL"]:
            os.environ.setdefault(key, "")

        logger.info("Initializing hexdoc.")

        props = Properties.load_data(
            props_dir=Path.cwd(),
            data={
                "modid": "hexbug",
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

        logger.info("Loading resources.")

        with ModResourceLoader.load_all(props, pm, export=False) as loader:
            logger.info("Loading metadata.")

            hexdoc_metadatas = loader.load_metadata(model_type=HexdocMetadata)
            pattern_metadatas = loader.load_metadata(
                name_pattern="{modid}.patterns",
                model_type=PatternMetadata,
                allow_missing=True,
            )

            logger.info("Loading i18n.")

            i18n = I18n.load(loader, enabled=True, lang="en_us")

            logger.info("Loading book.")

            book_id, book_data = book_plugin.load_book_data(props.book_id, loader)
            context = init_context(
                book_id=book_id,
                book_data=book_data,
                pm=pm,
                loader=loader,
                i18n=i18n,
                all_metadata=hexdoc_metadatas,
            )

            # patch book context to force all links to include the book url
            book_context = HexBugBookContext(**dict(BookContext.of(context)))
            book_context.add_to_context(context, overwrite=True)

            book = book_plugin.validate_book(book_data, context=context)
            assert isinstance(book, Book)

        # Jinja stuff

        jinja_env = create_jinja_env_with_loader(PackageLoader("hexdoc", "_templates"))
        jinja_env.autoescape = False
        styled_template = jinja_env.from_string(
            r"""
            {%- import "macros/formatting.md.jinja" as fmt with context -%}
            {{- fmt.styled(text)|replace("\\n", "\n") if text else "" -}}
            """,
            globals={
                "book_links": book_context.book_links,
            },
        )

        # get pattern book info

        logger.info("Finding pattern pages.")

        op_pattern_pages = defaultdict[ResourceLocation, list["_PatternBookInfo"]](list)
        raw_pattern_pages = defaultdict[str, list["_PatternBookInfo"]](list)

        for category in book.categories.values():
            for entry in category.entries.values():
                for page, next_page in zip_longest(entry.pages, entry.pages[1:]):
                    if not isinstance(next_page, TextPage):
                        next_page = None

                    # use PageWithOpPattern instead of LookupPatternPage so we can find special handler pages
                    # eg. Bookkeeper's Gambit (op_id=hexcasting:mask)
                    if isinstance(page, PageWithOpPattern):
                        op_pattern_pages[page.op_id].append((entry, page, next_page))

                    if isinstance(page, (ManualOpPatternPage, ManualRawPatternPage)):
                        for pattern in page.patterns:
                            raw_pattern_pages[pattern.signature].append(
                                (entry, page, next_page)
                            )

        # load mods

        for static_info in STATIC_MOD_INFO:
            mod_id = static_info.id
            logger.info(f"Loading mod: {mod_id}")

            mod_plugin = pm.mod_plugin(mod_id, book=True)
            hexdoc_metadata = hexdoc_metadatas[mod_id]

            if hexdoc_metadata.book_url is None:
                raise ValueError(f"Mod missing book url: {mod_id}")

            _, author, repo, commit = hexdoc_metadata.asset_url.parts

            registry._register_mod(
                ModInfo.from_parts(
                    static_info,
                    DynamicModInfo(
                        version=mod_plugin.mod_version,
                        book_url=hexdoc_metadata.book_url,
                        github_author=author,
                        github_repo=repo,
                        github_commit=commit,
                    ),
                )
            )

        pattern_infos = [
            pattern_info
            for pattern_metadata in pattern_metadatas.values()
            for pattern_info in pattern_metadata.patterns
        ] + EXTRA_PATTERNS

        for pattern_info in pattern_infos:
            pattern = PatternInfo(
                id=pattern_info.id,
                # don't want to use the book-specific translation here
                name=i18n.localize(
                    f"hexcasting.action.{pattern_info.id}",
                    f"hexcasting.rawhook.{pattern_info.id}",
                ).value,
                direction=HexDir[pattern_info.startdir.name],
                signature=pattern_info.signature,
                is_per_world=pattern_info.is_per_world,
                operators=[],
            )

            known_inputs = dict[str | None, PatternOperator]()
            for entry, page, next_page in (
                op_pattern_pages[pattern.id] + raw_pattern_pages[pattern.signature]
            ):
                # use the mod that the entry came from, not the mod of the pattern
                # eg. MoreIotas adds operators for hexcasting:add
                # in that case, mod should be MoreIotas, not Hex Casting
                mod = registry.mods[entry.id.namespace]

                text = page.text or (next_page and next_page.text)
                if text:
                    description = styled_template.render(
                        text=text,
                        page_url=str(mod.book_url),
                    ).strip()
                else:
                    description = None

                url_key = page.book_link_key(entry.book_link_key)
                if url_key is None:
                    raise ValueError(
                        f"Page missing anchor for pattern {pattern.id} in entry {entry.id}: {page}"
                    )

                book_url = book_context.book_links.get(url_key)
                if book_url is None:
                    raise ValueError(
                        f"Failed to get book_url of page for pattern {pattern.id} in entry {entry.id}: {page}"
                    )

                op = PatternOperator(
                    name=str(page.header),
                    description=description,
                    inputs=page.input,
                    outputs=page.output,
                    book_url=book_url,
                    mod_id=mod.id,
                )

                if other := known_inputs.get(op.inputs):
                    raise ValueError(
                        f"Multiple operators found for pattern {pattern.id} with inputs {op.inputs}:\n  {op}\n  {other}"
                    )

                known_inputs[op.inputs] = op
                pattern.operators.append(op)

            if not pattern.operators:
                raise ValueError(f"No operators found for pattern: {pattern.id}")

            registry._register_pattern(pattern)

        logger.info("Done.")
        return registry

    @classmethod
    def load(cls, path: Path) -> Self:
        data = path.read_text(encoding="utf-8")
        return cls.model_validate_json(data)

    def save(self, path: Path, *, indent: int | None = None):
        data = self.model_dump_json(round_trip=True, indent=indent)
        path.write_text(data, encoding="utf-8")

    def _register_mod(self, mod: ModInfo):
        if mod.id in self.mods:
            raise ValueError(f"Mod is already registered: {mod.id}")

        self.mods[mod.id] = mod

    def _register_pattern(self, pattern: PatternInfo):
        if pattern.id in self.patterns:
            raise ValueError(f"Pattern is already registered: {pattern.id}")

        self.patterns[pattern.id] = pattern
