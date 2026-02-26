from __future__ import annotations

import logging
from functools import cached_property
from pathlib import Path
from typing import Any, override

from hexdoc.core import Properties, ResourceLocation
from hexdoc.core.resource_dir import PathResourceDir
from hexdoc.minecraft.i18n import I18n, LocalizedStr
from hexdoc.patchouli import BookContext
from hexdoc.patchouli.entry import Entry
from hexdoc.utils import TRACE, JSONDict, classproperty
from yarl import URL

logger = logging.getLogger(__name__)


class HexBugProperties(Properties):
    """Subclass of Properties to prevent using git to get the cache dir."""

    @classproperty
    @classmethod
    @override
    def context_key(cls) -> str:  # pyright: ignore[reportIncompatibleVariableOverride]
        return Properties.context_key

    @cached_property
    @override
    def repo_root(self):
        return Path.cwd()


class HexBugBookContext(BookContext):
    """Subclass of BookContext to force all book links to include the book url."""

    @classproperty
    @classmethod
    @override
    def context_key(cls) -> str:  # pyright: ignore[reportIncompatibleVariableOverride]
        return BookContext.context_key

    @override
    def get_link_base(self, resource_dir: PathResourceDir) -> URL:
        modid = resource_dir.modid
        if modid is None:
            raise RuntimeError(
                f"Failed to get link base of resource dir with no modid (this should never happen): {resource_dir}"
            )

        book_url = self.all_metadata[modid].book_url
        if book_url is None:
            raise ValueError(f"Mod {modid} does not export a book url")

        return book_url


# TODO: remove if hexic is removed
# terrible awful bad
def monkeypatch_hexdoc():
    currently_loading_hexic_content = False

    original_load = Entry.load
    original_localize = I18n.localize

    def load_patched(
        cls: type[Entry],
        resource_dir: PathResourceDir,
        id: ResourceLocation,
        data: JSONDict,
        context: dict[str, Any],
    ) -> Any:
        nonlocal currently_loading_hexic_content

        if resource_dir.modid == "hexic":
            currently_loading_hexic_content = True

        try:
            return original_load(resource_dir, id, data, context)
        finally:
            currently_loading_hexic_content = False

    def localize_patched(
        self: I18n,
        *keys: str,
        default: str | None = None,
        silent: bool = False,
    ) -> LocalizedStr:
        return original_localize(
            self,
            *keys,
            default=default,
            silent=silent or currently_loading_hexic_content,
        )

    Entry.load = classmethod(load_patched)  # pyright: ignore[reportAttributeAccessIssue]
    I18n.localize = localize_patched


# TODO: remove when the next Hex version is released (FallingColors/HexMod#1007)
def monkeypatch_hexdoc_hexcasting():
    from hexdoc_hexcasting.metadata import HexContext
    from hexdoc_hexcasting.utils.pattern import PatternInfo

    def _add_pattern_patched(
        self: HexContext,
        pattern: PatternInfo,
        signatures: dict[str, PatternInfo],
    ):
        logger.log(TRACE, f"Load pattern: {pattern.id}")

        if duplicate := self.patterns.get(pattern.id):
            raise ValueError(f"Duplicate pattern {pattern.id}\n{pattern}\n{duplicate}")

        if duplicate := signatures.get(pattern.signature):
            logger.warning(f"Duplicate pattern {pattern.id}\n{pattern}\n{duplicate}")

        self.patterns[pattern.id] = pattern
        signatures[pattern.signature] = pattern

    HexContext._add_pattern = _add_pattern_patched  # pyright: ignore[reportPrivateUsage]
