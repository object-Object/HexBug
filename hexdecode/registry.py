import re
from collections import defaultdict
from dataclasses import dataclass, field
from fractions import Fraction
from typing import TypeVar

from hexdecode.hex_math import Direction, Segment, get_rotated_aligned_pattern_segments
from utils.mods import Mod
from utils.parse_rational import parse_rational
from utils.patterns import parse_mask


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


@dataclass(frozen=True)
class RawPatternInfo:
    direction: Direction
    pattern: str


class DuplicatePatternException(Exception):
    def __init__(self, new_info: PatternInfo, old_info: PatternInfo) -> None:
        super().__init__(f"Duplicate pattern!\n{new_info}\n{old_info}")


T = TypeVar("T", str, None)
U = TypeVar("U")


hexpattern_re = re.compile(r"HexPattern\((.+)\)")
raw_pattern_re = re.compile(r"^(\S+)(?:\s+([aqwedAQWED]+))?$")
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

    def _insert_possible_duplicate(self, lookup: dict[U, PatternInfo], key: U, info: PatternInfo):
        if (other_info := lookup.get(key)) and other_info.name != info.name:
            raise DuplicatePatternException(info, other_info)
        lookup[key] = info

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

    def add_pattern(self, info: PatternInfo) -> None:
        self.patterns.append(info)
        self.from_name[info.name] = info
        self.from_display_name[info.display_name] = info

        if not isinstance(info, SpecialHandlerPatternInfo):
            if info.is_great:
                for segments in get_rotated_aligned_pattern_segments(info.direction, info.pattern):
                    self._insert_possible_duplicate(self.from_segments, segments, info)
            else:
                self._insert_possible_duplicate(self.from_pattern, info.pattern, info)

        self._insert_shorthand(info)

    def from_shorthand(self, shorthand: str) -> tuple[PatternInfo | RawPatternInfo, Fraction | int | str | None] | None:
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
