from __future__ import annotations

from functools import cached_property
from pathlib import Path
from typing import override

from hexdoc.core import Properties
from hexdoc.core.resource_dir import PathResourceDir
from hexdoc.patchouli import BookContext
from hexdoc.utils import classproperty
from yarl import URL


class HexBugProperties(Properties):
    """Subclass of Properties to prevent using git to get the cache dir."""

    @classproperty
    @classmethod
    @override
    def context_key(cls) -> str:
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
    def context_key(cls) -> str:
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
