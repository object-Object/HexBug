from dataclasses import dataclass
from fractions import Fraction
from typing import Any

from ..hexdecode.hex_math import Direction
from ..hexdecode.hexast import generate_bookkeeper
from ..hexdecode.registry import (
    InvalidSpecialHandlerArgumentException,
    Registry,
    SpecialHandler,
    SpecialHandlerArgument,
)
from ..hexdecode.special_handlers import (
    parse_bookkeeper,
    parse_numerical_reflection,
)
from .generate_decomposed_number import generate_decomposed_number
from .parse_rational import parse_rational
from .patterns import parse_mask

# hex casting


class NumberSpecialHandler(SpecialHandler):
    def parse_pattern(self, direction: Direction, pattern: str) -> Any | None:
        return parse_numerical_reflection(pattern)

    def parse_argument(self, value: str) -> SpecialHandlerArgument:
        return parse_rational(value)

    def parse_shorthand(self, shorthand: str) -> SpecialHandlerArgument:
        return parse_rational(shorthand)

    async def generate_pattern(
        self,
        registry: Registry,
        arg: SpecialHandlerArgument,
        should_align_horizontal: bool,
    ) -> list[tuple[Direction, str]] | None:
        if not isinstance(arg, (Fraction, int)):
            raise InvalidSpecialHandlerArgumentException(self.info.display_name)

        result = await generate_decomposed_number(
            registry, arg, should_align_horizontal
        )
        if result is None:
            raise InvalidSpecialHandlerArgumentException(
                f"{self.info.display_name}: {arg}"
            )

        return result[0]


class MaskSpecialHandler(SpecialHandler):
    def parse_pattern(self, direction: Direction, pattern: str) -> Any | None:
        return parse_bookkeeper(direction, pattern)

    def parse_argument(self, value: str) -> SpecialHandlerArgument:
        return parse_mask(value)

    def parse_shorthand(self, shorthand: str) -> SpecialHandlerArgument:
        return parse_mask(shorthand)

    async def generate_pattern(
        self,
        registry: Registry,
        arg: SpecialHandlerArgument,
        should_align_horizontal: bool,
    ) -> list[tuple[Direction, str]] | None:
        if not isinstance(arg, str):
            raise InvalidSpecialHandlerArgumentException(self.info.display_name)

        return [generate_bookkeeper(arg)]


# hexical


@dataclass(kw_only=True)
class TailDepthSpecialHandler(SpecialHandler):
    direction: Direction
    prefix: str
    initial_depth: int

    def parse_pattern(self, direction: Direction, pattern: str) -> Any | None:
        tail = pattern.removeprefix(self.prefix)
        if tail == pattern:
            return None

        depth = self.initial_depth
        for index, char in enumerate(tail):
            if char != "qe"[index % 2]:
                return None
            depth += 1

        return depth

    def parse_argument(self, value: str) -> SpecialHandlerArgument:
        # number, eg. Nephthys' Gambit: 3
        try:
            return int(value)
        except ValueError:
            pass

        # visual tail, eg. Nephthys' Gambit: ---
        if value == "-" * len(value):
            return len(value)

        return None

    async def generate_pattern(
        self,
        registry: Registry,
        arg: SpecialHandlerArgument,
        should_align_horizontal: bool,
    ) -> list[tuple[Direction, str]]:
        if not isinstance(arg, int) or arg < self.initial_depth:
            raise InvalidSpecialHandlerArgumentException(self.info.display_name)

        pattern = self.prefix
        for index in range(arg - self.initial_depth):
            pattern += "qe"[index % 2]

        return [(self.direction, pattern)]
