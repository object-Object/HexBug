import re
from collections import defaultdict
from dataclasses import dataclass, field
from fractions import Fraction
from typing import TypeVar

from ..utils.mods import Mod
from ..utils.parse_rational import parse_rational
from ..utils.patterns import parse_mask
from .hex_math import Direction, Segment, get_rotated_aligned_pattern_segments


@dataclass(frozen=True, kw_only=True, repr=False)
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

    def __repr__(self) -> str:
        return f"{self.mod.name}:{self.name}"

    @property
    def display_name(self) -> str:
        return self.name if self.translation is None else self.translation


@dataclass(frozen=True, kw_only=True, repr=False)
class NormalPatternInfo(_BasePatternInfo):
    direction: Direction
    pattern: str
    rotated_segments: tuple[frozenset[Segment]] = field(init=False)
    """Tuple of rotated aligned segment sets for this pattern. Empty if is_great is false."""

    def __post_init__(self):
        rotated_segments: tuple[frozenset[Segment], ...] = (
            tuple(get_rotated_aligned_pattern_segments(self.direction, self.pattern)) if self.is_great else tuple()
        )
        object.__setattr__(self, "rotated_segments", rotated_segments)


@dataclass(frozen=True, kw_only=True, repr=False)
class SpecialHandlerPatternInfo(_BasePatternInfo):
    direction: None = None
    pattern: None = None
    rotated_segments: None = None


PatternInfo = NormalPatternInfo | SpecialHandlerPatternInfo


@dataclass(frozen=True)
class RawPatternInfo:
    direction: Direction
    pattern: str


@dataclass
class DuplicatePatternException(Exception):
    info: PatternInfo
    duplicates: list[tuple[str, PatternInfo]]


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


@dataclass
class Registry:
    pregen_numbers: dict[int, tuple[Direction, str]]

    def __post_init__(self) -> None:
        self.patterns: list[PatternInfo] = []
        self.from_name: dict[str, PatternInfo] = {}
        self.from_display_name: dict[str, PatternInfo] = {}
        self.from_pattern: dict[str, PatternInfo] = {}
        self.from_segments: dict[frozenset[Segment], PatternInfo] = {}
        self._from_shorthand: dict[str, PatternInfo] = {}
        self.page_title_to_url: defaultdict[Mod, dict[str, tuple[str, list[str]]]] = defaultdict(dict)
        """mod: page_title: (url, names)"""

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

            if info.name == "mask":
                options.append("book")
            elif info.name == "open_paren":
                options.append("{")
                options.append("intro")
            elif info.name == "close_paren":
                options.append("}")
                options.append("retro")

            for option in options:
                option = option.strip()
                if option and option not in self._from_shorthand and option not in check_suffixes:
                    self._from_shorthand[option] = info

    def _ensure_not_duplicate(self, info: PatternInfo) -> None:
        """Ensures that this pattern doesn't yet exist in any of the registry lookups.

        Raises:
            DuplicatePatternException: If a conflict is found.
        """
        duplicates: list[tuple[str, PatternInfo]] = []

        def _add_dup_if_exists(attribute: str, duplicate: PatternInfo | None):
            if duplicate is not None:
                duplicates.append((attribute, duplicate))

        _add_dup_if_exists("name", self.from_name.get(info.name))
        _add_dup_if_exists("display_name", self.from_display_name.get(info.display_name))

        if not isinstance(info, SpecialHandlerPatternInfo):
            if info.is_great:
                for i, segments in enumerate(info.rotated_segments):
                    _add_dup_if_exists(f"segments[{i}]", self.from_segments.get(segments))
            else:
                _add_dup_if_exists("pattern", self.from_pattern.get(info.pattern))

        if duplicates:
            raise DuplicatePatternException(info, duplicates)

    def add_pattern(self, info: PatternInfo) -> None:
        """Insert a pattern into the registry.

        Raises:
            DuplicatePatternException: If the value of any lookup field already exists in the registry.
        """
        self._ensure_not_duplicate(info)

        self.patterns.append(info)
        self.from_name[info.name] = info
        self.from_display_name[info.display_name] = info

        if not isinstance(info, SpecialHandlerPatternInfo):
            if info.is_great:
                for segments in info.rotated_segments:
                    self.from_segments[segments] = info
            else:
                self.from_pattern[info.pattern] = info

        self._insert_shorthand(info)

    def from_shorthand(self, shorthand: str) -> tuple[PatternInfo | RawPatternInfo, Fraction | int | str | None] | None:
        # TODO: why doesn't this return a class?????
        shorthand = hexpattern_re.sub(lambda m: m.group(1), shorthand).lower().strip()

        if pattern := self._from_shorthand.get(shorthand):
            return pattern, None

        if (
            (match := special_handler_pattern_re.match(shorthand))
            and (pattern := self._from_shorthand.get(match.group(1)))
            and isinstance(pattern, SpecialHandlerPatternInfo)
        ):
            match pattern.name:
                case "number":
                    if (arg := parse_rational(match.group(2))) is not None:
                        return pattern, arg
                case "mask":
                    if (arg := parse_mask(match.group(2))) is not None:
                        return pattern, arg

        if (arg := parse_rational(shorthand)) is not None:
            return self.from_name["number"], arg

        if (arg := parse_mask(shorthand)) is not None:
            return self.from_name["mask"], arg

        if (match := raw_pattern_re.match(shorthand)) and (direction := Direction.from_shorthand(match.group(1))):
            return RawPatternInfo(direction, match.group(2) or ""), None

        return None

    def from_shorthand_list(
        self, all_shorthand: str
    ) -> tuple[list[tuple[PatternInfo | RawPatternInfo, Fraction | int | str | None]], list[str], str]:
        patterns: list[tuple[PatternInfo | RawPatternInfo, Fraction | int | str | None]] = []
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
