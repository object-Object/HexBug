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
