from __future__ import annotations

import logging
from functools import cached_property
from pathlib import Path
from typing import override

from hexdoc.core import Properties
from hexdoc.core.resource_dir import PathResourceDir
from hexdoc.patchouli import BookContext
from hexdoc.utils import TRACE, classproperty
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


# FIXME: hack
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
