from dataclasses import dataclass, field
from hexdecode.hex_math import Segment, Direction
from hexdecode.hex_math import get_rotated_pattern_segments
from utils.mods import Mod
from collections import defaultdict
from typing import TypeVar


@dataclass(frozen=True, kw_only=True)
class _BasePatternInfo:
    name: str
    translation: str | None
    mod: Mod
    path: str
    classname: str
    class_mod: Mod
    is_great: bool

    # late-initialized fields
    book_url: str | None = field(init=False, default=None)
    args: str | None = field(init=False, default=None)

    def __late_init__(self, book_url: str | None, args: str | None):
        object.__setattr__(self, "book_url", book_url)
        object.__setattr__(self, "args", args)

    @property
    def display_name(self) -> str:
        return self.name if self.translation is None else self.translation


@dataclass(frozen=True, kw_only=True)
class NormalPatternInfo(_BasePatternInfo):
    direction: Direction
    pattern: str


@dataclass(frozen=True, kw_only=True)
class SpecialHandlerPatternInfo(_BasePatternInfo):
    direction: None = None
    pattern: None = None


PatternInfo = NormalPatternInfo | SpecialHandlerPatternInfo


class DuplicatePatternException(Exception):
    def __init__(self, new_info: PatternInfo, old_info: PatternInfo) -> None:
        super().__init__(f"Duplicate pattern!\n{new_info}\n{old_info}")


T = TypeVar("T", str, None)
U = TypeVar("U")


class Registry:
    def __init__(self) -> None:
        self.patterns: list[PatternInfo] = []
        self.from_name: dict[str, PatternInfo] = {}
        self.from_display_name: dict[str, PatternInfo] = {}
        self.from_pattern: dict[str, PatternInfo] = {}
        self.from_segments: dict[frozenset[Segment], PatternInfo] = {}
        self.page_title_to_url: defaultdict[Mod, dict[str, tuple[str, list[str]]]] = defaultdict(dict)
        """mod: page_title: (url, names)"""

    def _insert_possible_duplicate(self, lookup: dict[U, PatternInfo], key: U, info: PatternInfo):
        if (other_info := lookup.get(key)) and other_info.name != info.name:
            raise DuplicatePatternException(info, other_info)
        lookup[key] = info

    def add_pattern(self, info: PatternInfo) -> None:
        self.patterns.append(info)
        self.from_name[info.name] = info
        self.from_display_name[info.display_name] = info
        if not isinstance(info, SpecialHandlerPatternInfo):
            if info.is_great:
                for segments in get_rotated_pattern_segments(info.direction, info.pattern):
                    self._insert_possible_duplicate(self.from_segments, segments, info)
            else:
                self._insert_possible_duplicate(self.from_pattern, info.pattern, info)

    def get_translation_from_name(self, name: str, default: T = None) -> str | T:
        if info := self.from_name.get(name):
            if info.translation is not None:
                return info.translation
        return default
