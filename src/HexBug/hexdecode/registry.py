from __future__ import annotations

import dataclasses
import re
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass, field
from fractions import Fraction
from functools import cached_property
from typing import Any, TypedDict, TypeVar, Unpack

from HexBug.hexdecode.hexast import PatternIota

from ..utils.mods import Mod
from .hex_math import (
    Direction,
    Segment,
    get_aligned_pattern_segments,
    get_rotated_aligned_pattern_segments,
)


@dataclass(frozen=True, kw_only=True, repr=False)
class _BasePatternInfo:
    name: str
    translation: str | None
    mod: Mod
    path: str | None
    classname: str | None
    class_mod: Mod | None
    is_great: bool
    shorthand_names: tuple[str, ...] = tuple()

    # late-initialized fields
    book_url: str | None = field(init=False, default=None)
    args: str | None = field(init=False, default=None)
    description: str | None = field(init=False, default=None)

    def __late_init__(
        self,
        *,
        book_url: str | None,
        args: str | None,
        description: str | None,
    ):
        object.__setattr__(self, "book_url", book_url)
        object.__setattr__(self, "args", args)
        object.__setattr__(self, "description", description)

    def __repr__(self) -> str:
        return f"{self.mod.name}:{self.name}"

    @property
    def display_name(self) -> str:
        return self.name if self.translation is None else self.translation

    @property
    def id(self):
        return f"{self.mod.value.modid}:{self.name}"


@dataclass(frozen=True, kw_only=True, repr=False)
class NormalPatternInfo(_BasePatternInfo):
    direction: Direction
    pattern: str

    def print(self):
        return self.display_name

    @cached_property
    def rotated_segments(self):
        return tuple(get_rotated_aligned_pattern_segments(self.direction, self.pattern))


SpecialHandlerArgument = Fraction | int | str | None


class InvalidSpecialHandlerArgumentException(Exception):
    def __init__(self, display: str, *args: object) -> None:
        super().__init__(f"Invalid special handler argument: {display}", *args)
        self.display = display


class SpecialHandler(ABC):
    def __init__(self) -> None:
        self.info: SpecialHandlerPatternInfo

    @abstractmethod
    def parse_pattern(self, direction: Direction, pattern: str) -> Any | None:
        """Attempts to parse an unknown pattern with this handler.

        Returns None if the pattern does not match this handler.
        """

    @abstractmethod
    def parse_argument(self, value: str) -> SpecialHandlerArgument:
        """Attempts to parse the argument for this pattern."""

    @abstractmethod
    async def generate_pattern(
        self,
        registry: Registry,
        arg: SpecialHandlerArgument,
        should_align_horizontal: bool,
    ) -> list[tuple[Direction, str]]:
        ...

    def parse_shorthand(self, shorthand: str) -> SpecialHandlerArgument:
        """Attempts to parse a full shorthand pattern into an argument for this
        pattern.

        Optional.
        """
        return None


@dataclass(frozen=True, kw_only=True, repr=False)
class SpecialHandlerPatternInfo(_BasePatternInfo):
    direction: Direction | None = None
    pattern: str | None = None
    rotated_segments: None = None
    value: Any | None = None
    handler: SpecialHandler | None = None

    def __post_init__(self):
        if self.handler:
            self.handler.info = self

    def print(self):
        if self.value is None:
            return self.display_name
        return f"{self.display_name}: {self.value}"


PatternInfo = NormalPatternInfo | SpecialHandlerPatternInfo

ShorthandPattern = tuple[PatternInfo | PatternIota, SpecialHandlerArgument]


@dataclass(frozen=True)
class DuplicatePattern:
    info: PatternInfo
    attribute: str
    value: Any


@dataclass
class DuplicatePatternException(Exception):
    info: PatternInfo | None
    duplicates: list[DuplicatePattern]


T = TypeVar("T", str, None)
U = TypeVar("U")


hexpattern_re = re.compile(r"HexPattern\((.+)\)")
raw_pattern_re = re.compile(r"^(\S+)(?:\s+([aqwedsAQWEDS]+))?$")
special_handler_pattern_re = re.compile(r"^(.+)(?<!:)(?::\s*|\s+)(.+?)$")

suffixes: list[tuple[str, list[str]]] = [
    (" reflection", [" ref", " refl"]),
    (" purification", [" pur", " prfn", " prf"]),
    (" distillation", [" dist", " distill"]),
    (" exaltation", [" ex", " exalt"]),
    (" decomposition", [" dec", " decomp"]),
    (" disintegration", [" dis", " disint"]),
    (" gambit", [" gam"]),
]
check_suffixes = {s.strip() for old, all_new in suffixes for s in [old] + all_new}


class DuplicateCheckerKwargs(TypedDict):
    name: str | None
    translation: str | None
    pattern: str | None
    is_great: bool | None


@dataclass
class Registry:
    pregen_numbers: dict[int, tuple[Direction, str]]

    def __post_init__(self) -> None:
        self.patterns: list[PatternInfo] = []
        self.from_name: dict[str, PatternInfo] = {}
        self.from_display_name: dict[str, PatternInfo] = {}
        self.from_pattern: dict[str, PatternInfo] = {}
        self.from_segments: dict[frozenset[Segment], PatternInfo] = {}
        """Only great spells."""
        self._from_segments_total: defaultdict[
            frozenset[Segment], set[PatternInfo]
        ] = defaultdict(set)
        """Includes non-great spells."""
        self._from_shorthand: dict[str, PatternInfo] = {}
        self.page_title_to_url: defaultdict[
            Mod, dict[str, tuple[str, list[str]]]
        ] = defaultdict(dict)
        """mod: page_title: (url, names)"""
        self.special_handlers: list[SpecialHandler] = []

    def _insert_shorthand(self, info: PatternInfo):
        self._from_shorthand[info.name.lower()] = info

        if translation := info.translation:
            options = [translation.lower()]

            for option in options:
                for old, all_new in suffixes:
                    if old in option:
                        for new in all_new + [""]:
                            options.append(option.replace(old, new))

            for option in options:
                for old, all_new in [
                    ("vector ", ["vec "]),
                ]:
                    if old in option:
                        for new in all_new + [""]:
                            options.append(option.replace(old, new))

            for option in options:
                if "'s" in option:
                    options.append(option.replace("'s", ""))
                if "s'" in option:
                    options.append(option.replace("s'", "s"))

            for option in options:
                if ":" in option:
                    options.append(option.replace(":", ""))

            for option in options:
                if "ii" in option:
                    options.append(option.replace("ii", "2"))

            if info.shorthand_names:
                options.extend(info.shorthand_names)

            for option in options:
                option = option.strip()
                if (
                    option
                    and option not in self._from_shorthand
                    and option not in check_suffixes
                ):
                    self._from_shorthand[option] = info

    # TODO: scuffed
    def ensure_not_duplicate(
        self,
        *,
        info: PatternInfo | None = None,
        **kwargs: Unpack[DuplicateCheckerKwargs],
    ):
        """Ensures that this pattern doesn't yet exist in any of the registry lookups.

        `info` is only used when raising exceptions.

        Raises:
            DuplicatePatternException: If a conflict is found.
        """
        if duplicates := self.get_duplicates(**kwargs):
            raise DuplicatePatternException(info, duplicates)

    def get_duplicates(self, **kwargs: Unpack[DuplicateCheckerKwargs]):
        duplicates = [
            DuplicatePattern(
                attribute=attribute,
                info=info,
                value=value,
            )
            for attribute, info, value in self._get_possible_duplicates(**kwargs)
            if info is not None
        ]
        duplicates.sort(key=lambda v: (v.info.display_name, v.attribute))
        return duplicates

    def _get_possible_duplicates(
        self,
        *,
        name: str | None,
        translation: str | None,
        pattern: str | None,
        is_great: bool | None,
    ):
        """yields (attribute, pattern_info, duplicate_value)"""

        if name is not None:
            yield "name", self.from_name.get(name), name

        display_name = translation if translation is not None else name
        if display_name is not None:
            yield "display_name", self.from_display_name.get(display_name), display_name

        if pattern is not None:
            yield "pattern", self.from_pattern.get(pattern), pattern

            segments = get_aligned_pattern_segments(Direction.EAST, pattern)
            if is_great:
                # great spells must not match the shape of ANY pattern
                infos = self._from_segments_total[segments]
            else:
                # non-great-spells must not match the shape of any great spell
                # but they can match the shape of other patterns
                infos = [self.from_segments.get(segments)]

            for info in infos:
                yield "shape", info, segments

    def add_pattern(self, info: PatternInfo) -> None:
        """Insert a pattern into the registry.

        Raises:
            DuplicatePatternException: If the value of any lookup field already exists in the registry.
        """

        self.ensure_not_duplicate(
            info=info,
            name=info.name,
            translation=info.translation,
            pattern=info.pattern,
            is_great=info.is_great,
        )

        self.patterns.append(info)
        self.from_name[info.name] = info
        self.from_display_name[info.display_name] = info

        if isinstance(info, SpecialHandlerPatternInfo):
            if info.handler:
                self.special_handlers.append(info.handler)
        else:
            for segments in info.rotated_segments:
                self._from_segments_total[segments].add(info)

            if info.is_great:
                for segments in info.rotated_segments:
                    self.from_segments[segments] = info
            else:
                self.from_pattern[info.pattern] = info

        self._insert_shorthand(info)

    def from_shorthand(self, shorthand: str) -> ShorthandPattern | None:
        # TODO: why doesn't this return a class?????
        shorthand = hexpattern_re.sub(lambda m: m.group(1), shorthand).lower().strip()

        if pattern := self._from_shorthand.get(shorthand):
            return pattern, None

        if (
            (match := special_handler_pattern_re.match(shorthand))
            and (pattern := self._from_shorthand.get(match.group(1)))
            and isinstance(pattern, SpecialHandlerPatternInfo)
            and pattern.handler
            and (arg := pattern.handler.parse_argument(match.group(2))) is not None
        ):
            return pattern, arg

        for handler in self.special_handlers:
            if (arg := handler.parse_shorthand(shorthand)) is not None:
                return handler.info, arg

        if (match := raw_pattern_re.match(shorthand)) and (
            direction := Direction.from_shorthand(match.group(1))
        ):
            return PatternIota(direction, match.group(2) or ""), None

        return None

    # FIXME: what the hell
    def from_shorthand_list(
        self, all_shorthand: str
    ) -> tuple[list[ShorthandPattern], list[str], str]:
        """Returns: patterns, unknown, pretty_shorthand"""

        patterns: list[ShorthandPattern] = []
        unknown: list[str] = []

        split = [stripped for s in all_shorthand.split(",") if (stripped := s.strip())]
        for shorthand in split:
            if pattern := self.from_shorthand(shorthand):
                patterns.append(pattern)
            else:
                unknown.append(shorthand)

        return patterns, unknown, ", ".join(split)

    def get_translation_from_name(self, name: str, default: T = None) -> str | T:
        if info := self.from_name.get(name):
            if info.translation is not None:
                return info.translation
        return default

    def from_pattern_or_segments(self, direction: Direction, pattern: str):
        if info := self.from_pattern.get(pattern):
            return info

        segments = get_aligned_pattern_segments(direction, pattern)
        return self.from_segments.get(segments)

    def parse_unknown_pattern(self, direction: Direction, pattern: str):
        if info := self.from_pattern_or_segments(direction, pattern):
            return info

        for handler in self.special_handlers:
            value = handler.parse_pattern(direction, pattern)
            if value is not None:
                return dataclasses.replace(
                    handler.info,
                    direction=direction,
                    pattern=pattern,
                    value=value,
                )

        return None
