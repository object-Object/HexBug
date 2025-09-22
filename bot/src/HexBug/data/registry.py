from __future__ import annotations

import itertools
import logging
import os
from collections import defaultdict
from itertools import zip_longest
from pathlib import Path
from typing import Any, Self, overload

from hexdoc.cli.utils import init_context
from hexdoc.core import (
    MinecraftVersion,
    ModResourceLoader,
    ResourceLocation,
)
from hexdoc.data import HexdocMetadata
from hexdoc.jinja.render import create_jinja_env_with_loader
from hexdoc.minecraft import I18n
from hexdoc.patchouli import Book, BookContext
from hexdoc.patchouli.page import TextPage
from hexdoc.plugin import PluginManager
from jinja2 import PackageLoader
from pydantic import BaseModel, PrivateAttr, TypeAdapter, model_validator

from HexBug.data.lookups import PatternLookups
from HexBug.resources import load_resource
from HexBug.utils.hexdoc import (
    HexBugBookContext,
    HexBugProperties,
    monkeypatch_hexdoc_hexcasting,
)

from .hex_math import HexDir, HexPattern, PatternSignature
from .mods import DynamicModInfo, ModInfo
from .patterns import PatternInfo, PatternOperator
from .special_handlers import SpecialHandlerInfo, SpecialHandlerMatch
from .static_data import (
    DISABLED_PAGES,
    DISABLED_PATTERNS,
    DISAMBIGUATED_PATTERNS,
    EXTRA_PATTERNS,
    HEXDOC_PROPS,
    MODS,
    PATTERN_NAME_OVERRIDES,
    SPECIAL_HANDLERS,
    UNDOCUMENTED_PATTERNS,
)

logger = logging.getLogger(__name__)


type PatternMatchResult = PatternInfo | SpecialHandlerMatch[Any]


class HexBugRegistry(BaseModel):
    mods: dict[str, ModInfo]
    patterns: dict[ResourceLocation, PatternInfo]
    """The primary source of truth for patterns in this registry.

    IMPORTANT: If accessing this directly, make sure to check `pattern.display_as`
    and/or `pattern.is_hidden` as necessary.
    """
    special_handlers: dict[ResourceLocation, SpecialHandlerInfo]

    _lookups: PatternLookups = PrivateAttr(default_factory=PatternLookups)
    _pregenerated_numbers: dict[int, HexPattern] = PrivateAttr(
        default_factory=lambda: {}
    )

    @classmethod
    def build(cls) -> Self:
        logger.info("Building HexBug registry.")

        monkeypatch_hexdoc_hexcasting()

        # lazy imports because these won't be available when the bot runs
        from hexdoc_hexcasting.book.page import (
            ManualOpPatternPage,
            ManualRawPatternPage,
            PageWithOpPattern,
            PageWithPattern,
        )
        from hexdoc_hexcasting.metadata import PatternMetadata
        from hexdoc_hexcasting.utils.pattern import PatternInfo as HexdocPatternInfo
        from hexdoc_lapisworks.book.pages.pages import LookupPWShapePage

        registry = cls(
            mods={},
            patterns={},
            special_handlers={},
        )

        # load hexdoc data

        for key in ["GITHUB_SHA", "GITHUB_REPOSITORY", "GITHUB_PAGES_URL"]:
            os.environ.setdefault(key, "")

        logger.info("Initializing hexdoc.")

        props = HexBugProperties.load_data(props_dir=Path.cwd(), data=HEXDOC_PROPS)
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
            {{- fmt.styled(text) if text else "" -}}
            """,
            globals={
                "book_links": book_context.book_links,
            },
        )

        # load mods

        for static_info in MODS:
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

        # get pattern book info

        logger.info("Finding pattern pages.")

        id_ops = defaultdict[ResourceLocation, list[PatternOperator]](list)
        signature_ops = defaultdict[str, list[PatternOperator]](list)
        lapisworks_per_world_shapes = dict[ResourceLocation, HexdocPatternInfo]()

        for category in book.categories.values():
            for entry in category.entries.values():
                for page, next_page in zip_longest(entry.pages, entry.pages[1:]):
                    if not isinstance(page, PageWithPattern):
                        continue

                    if (fragment := page.fragment(entry.fragment)) in DISABLED_PAGES:
                        logger.info(f"Skipping disabled page: {fragment}")
                        continue

                    if not isinstance(next_page, TextPage):
                        next_page = None

                    # use the mod that the entry came from, not the mod of the pattern
                    # eg. MoreIotas adds operators for hexcasting:add
                    # in that case, mod should be MoreIotas, not Hex Casting
                    assert entry.resource_dir.modid is not None
                    mod = registry.mods[entry.resource_dir.modid]

                    text = page.text or (next_page and next_page.text)
                    if text:
                        description = styled_template.render(
                            text=text,
                            page_url=str(mod.book_url),
                        ).strip()
                    else:
                        description = None

                    url_key = page.book_link_key(entry.book_link_key)
                    book_url = book_context.book_links.get(url_key) if url_key else None

                    operator = PatternOperator(
                        description=description,
                        inputs=page.input,
                        outputs=page.output,
                        book_url=book_url,
                        mod_id=mod.id,
                    )

                    # use PageWithOpPattern instead of LookupPatternPage so we can find special handler pages
                    # eg. Bookkeeper's Gambit (op_id=hexcasting:mask)
                    if isinstance(page, PageWithOpPattern):
                        id_ops[page.op_id].append(operator)

                    if isinstance(page, (ManualOpPatternPage, ManualRawPatternPage)):
                        for pattern in page.patterns:
                            signature_ops[pattern.signature].append(operator)

                    # lapisworks per-world shapes
                    if isinstance(page, LookupPWShapePage):
                        lapisworks_per_world_shapes[page.op_id] = page.patterns[0]

        # load patterns

        logger.info("Loading patterns.")

        for pattern_info in itertools.chain(
            # hack: do these first so we can validate display_as
            lapisworks_per_world_shapes.values(),
            (
                pattern_info
                for pattern_metadata in pattern_metadatas.values()
                for pattern_info in pattern_metadata.patterns
            ),
            EXTRA_PATTERNS,
        ):
            if pattern_info.id in DISABLED_PATTERNS:
                logger.info(f"Skipping disabled pattern: {pattern_info.id}")
                continue

            display_as = None
            for other in lapisworks_per_world_shapes.keys():
                if (
                    pattern_info.id.namespace == other.id.namespace
                    and pattern_info.id.path.startswith(other.id.path)
                    and pattern_info.id.path.removeprefix(other.id.path).isnumeric()
                ):
                    display_as = other
                    break

            can_be_undocumented = (
                display_as is not None or pattern_info.id in UNDOCUMENTED_PATTERNS
            )

            name = i18n.localize(
                f"hexcasting.action.{pattern_info.id}",
                f"hexcasting.rawhook.{pattern_info.id}",
                silent=can_be_undocumented,
            ).value
            if override_name := PATTERN_NAME_OVERRIDES.get(pattern_info.id):
                logger.info(
                    f"Renaming pattern from {name} to {override_name}: {pattern_info.id}"
                )
                name = override_name
            elif pattern_info.id in DISAMBIGUATED_PATTERNS:
                mod = registry.mods[pattern_info.id.namespace]
                logger.info(
                    f"Appending mod name ({mod.name}) to pattern name ({name}): {pattern_info.id}"
                )
                name += f" ({mod.name})"

            pattern = PatternInfo(
                id=pattern_info.id,
                # don't want to use the book-specific translation here
                name=name,
                direction=HexDir[pattern_info.startdir.name],
                signature=pattern_info.signature,
                is_per_world=pattern_info.is_per_world,
                display_only=pattern_info.id in lapisworks_per_world_shapes,
                display_as=display_as,
                operators=[],
            )

            known_inputs = dict[str | None, PatternOperator]()
            for op in id_ops[pattern.id] + signature_ops[pattern.signature]:
                if other := known_inputs.get(op.inputs):
                    raise ValueError(
                        f"Multiple operators found for pattern {pattern.id} with inputs {op.inputs}:\n  {op}\n  {other}"
                    )

                if op.book_url is None:
                    logger.warning(
                        f"Failed to get book url for operator of pattern {pattern.id}: {op}"
                    )

                known_inputs[op.inputs] = op
                pattern.operators.append(op)

            if not (pattern.operators or can_be_undocumented):
                logger.warning(f"No operators found for pattern: {pattern.id}")

            pattern.operators.sort(
                key=lambda op: (
                    # using pattern instead of pattern_info causes a type error here???
                    0 if op.mod_id == pattern_info.id.namespace else 1,
                    op.inputs,
                ),
            )

            registry._register_pattern(pattern)

        logger.info("Loading special handlers.")

        for special_handler in SPECIAL_HANDLERS.values():
            ops = id_ops.get(special_handler.id)
            match ops:
                case [op]:
                    pass
                case None | []:
                    raise ValueError(
                        f"Failed to get book info for special handler: {special_handler.id}"
                    )
                case _:
                    raise ValueError(
                        f"Too many book pages found for special handler {special_handler.id} (expected 1, got {len(ops)}):\n  "
                        + "\n  ".join(str(op) for op in ops)
                    )

            raw_name = special_handler.localize(i18n).value

            for info in registry.patterns.values():
                if info.is_per_world:
                    continue
                if (value := special_handler.try_match(info.pattern)) is not None:
                    logger.warning(
                        f"Special handler {special_handler.id} conflicts with pattern {info.id} (value: {value})"
                    )

            registry._register_special_handler(
                SpecialHandlerInfo(
                    id=special_handler.id,
                    raw_name=raw_name,
                    base_name=special_handler.get_name(raw_name, value=None),
                    operator=op,
                )
            )

        # attempt to detect unregistered patterns with documentation (usually special handlers)
        for pattern_id in id_ops.keys():
            if (
                pattern_id not in registry.patterns
                and pattern_id not in registry.special_handlers
                and pattern_id not in DISABLED_PATTERNS
            ):
                logger.warning(f"Unregistered pattern: {pattern_id}")

        logger.info("Calculating registry stats.")

        for pattern in registry.patterns.values():
            if pattern.display_only:
                continue

            registry.mods[pattern.mod_id].pattern_count += 1
            if pattern.is_documented:
                registry.mods[pattern.mod_id].documented_pattern_count += 1

            for operator in pattern.operators:
                op_mod = registry.mods[operator.mod_id]
                if pattern.mod_id == operator.mod_id:
                    op_mod.first_party_operator_count += 1
                else:
                    op_mod.third_party_operator_count += 1

        for info in registry.special_handlers.values():
            registry.mods[info.mod_id].special_handler_count += 1

        logger.info("Done.")
        return registry

    @classmethod
    def load(cls, path: Path) -> Self:
        logger.info(f"Loading registry from file: {path}")
        data = path.read_text(encoding="utf-8")
        return cls.model_validate_json(data)

    def save(self, path: Path, *, indent: int | None = None):
        data = self.model_dump_json(round_trip=True, indent=indent)
        path.write_text(data, encoding="utf-8")

    @property
    def lookups(self):
        return self._lookups

    @property
    def pregenerated_numbers(self):
        return self._pregenerated_numbers

    @overload
    def try_match_pattern(
        self,
        pattern: HexPattern,
        /,
    ) -> PatternMatchResult | None: ...

    @overload
    def try_match_pattern(
        self,
        direction: HexDir,
        signature: str,
        /,
    ) -> PatternMatchResult | None: ...

    def try_match_pattern(
        self,
        direction_or_pattern: HexDir | HexPattern,
        signature: str | None = None,
        /,
    ) -> PatternMatchResult | None:
        # https://github.com/FallingColors/HexMod/blob/ef2cd28b2a/Common/src/main/java/at/petrak/hexcasting/common/casting/PatternRegistryManifest.java#L93

        match direction_or_pattern:
            case HexPattern() as pattern:
                pass
            case HexDir() as direction:
                assert signature is not None
                pattern = HexPattern(direction, signature)

        # normal patterns
        if info := self.lookups.signature.get(pattern.signature):
            return info

        # per world patterns (eg. Create Lava)
        if info := self.lookups.per_world_segments.get(pattern.get_aligned_segments()):
            return info

        # special handlers (eg. Numerical Reflection)
        for special_handler in SPECIAL_HANDLERS.values():
            if (value := special_handler.try_match(pattern)) is not None:
                return SpecialHandlerMatch[Any].from_parts(
                    handler=special_handler,
                    info=self.special_handlers[special_handler.id],
                    value=value,
                )

        return None

    @overload
    def display_pattern(
        self,
        info: PatternInfo,
    ) -> PatternInfo: ...

    @overload
    def display_pattern(
        self,
        info: SpecialHandlerMatch[Any],
    ) -> SpecialHandlerMatch[Any]: ...

    @overload
    def display_pattern(
        self,
        info: PatternInfo | SpecialHandlerMatch[Any],
    ) -> PatternInfo | SpecialHandlerMatch[Any]: ...

    def display_pattern(
        self,
        info: PatternInfo | SpecialHandlerMatch[Any],
    ) -> PatternInfo | SpecialHandlerMatch[Any]:
        """If the given pattern has a value for `display_as`, returns the referenced
        pattern; otherwise, returns the input unchanged."""
        match info:
            case PatternInfo(display_as=display_as) if display_as is not None:
                return self.patterns[display_as]
            case _:
                return info

    def _register_mod(self, mod: ModInfo):
        if mod.id in self.mods:
            raise ValueError(f"Mod is already registered: {mod.id}")
        self.mods[mod.id] = mod

    def _register_pattern(self, pattern: PatternInfo):
        if pattern.id in self.patterns:
            raise ValueError(f"Pattern is already registered: {pattern.id}")
        if pattern.display_as is not None and pattern.display_as not in self.patterns:
            raise ValueError(f"Broken display_as: {pattern.id} -> {pattern.display_as}")
        self.patterns[pattern.id] = pattern
        self.lookups.add_pattern(pattern)

    def _register_special_handler(self, info: SpecialHandlerInfo):
        if info.id in self.special_handlers:
            raise ValueError(f"Special handler is already registered: {info.id}")
        self.special_handlers[info.id] = info
        self.lookups.add_special_handler(info)

    @model_validator(mode="after")
    def _post_root(self):
        for pattern in self.patterns.values():
            self.lookups.add_pattern(pattern)
        for info in self.special_handlers.values():
            self.lookups.add_special_handler(info)

        ta = TypeAdapter(dict[int, tuple[HexDir, PatternSignature]])
        data = ta.validate_json(load_resource("numbers_2000.json"))
        for n, (direction, signature) in data.items():
            self.pregenerated_numbers[n] = HexPattern(direction, signature)

        return self
