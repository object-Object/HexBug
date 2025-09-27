from __future__ import annotations

import math
from contextvars import ContextVar
from dataclasses import dataclass
from datetime import timedelta
from fractions import Fraction
from typing import Sequence

from hexnumgen import AStarOptions, generate_number_pattern

from HexBug.data.hex_math import HexDir, HexPattern
from HexBug.utils.context import set_contextvar

_literals_var = ContextVar[dict[int, HexPattern]]("_literals_var")


ONE = HexPattern(HexDir.SOUTH_EAST, "aqaaw")
NEGATIVE_ONE = HexPattern(HexDir.NORTH_EAST, "deddw")

ADD = HexPattern(HexDir.NORTH_EAST, "waaw")
SUB = HexPattern(HexDir.NORTH_WEST, "wddw")
MUL = HexPattern(HexDir.SOUTH_EAST, "waqaw")
DIV = HexPattern(HexDir.NORTH_EAST, "wdedw")
POW = HexPattern(HexDir.NORTH_WEST, "wedew")


@dataclass(frozen=True, kw_only=True)
class DecomposedNumber:
    value: float
    equation: str
    patterns: Sequence[HexPattern]

    @classmethod
    def one(cls) -> DecomposedNumber:
        return cls.simple(1, ONE)

    @classmethod
    def negative_one(cls) -> DecomposedNumber:
        return cls.simple(-1, NEGATIVE_ONE)

    @classmethod
    def simple(cls, value: float, pattern: HexPattern):
        return cls(value=value, equation=str(value), patterns=[pattern])

    @classmethod
    def generate_or_decompose(
        cls,
        target: int | Fraction,
        literals: dict[int, HexPattern],
        timeout: timedelta | None,
    ):
        if result := generate_number_pattern(
            Fraction(target).as_integer_ratio(),
            trim_larger=False,
            allow_fractions=True,
            options=AStarOptions(
                timeout=timeout,
            ),
        ):
            return cls.simple(
                float(target),
                HexPattern(HexDir[result.direction], result.pattern),
            )

        with set_contextvar(_literals_var, literals):
            match target:
                case Fraction(numerator=numerator, denominator=denominator):
                    return cls._decompose(numerator) / cls._decompose(denominator)
                case int():
                    return cls._decompose(target)

    @classmethod
    def _decompose(cls, target: int) -> DecomposedNumber:
        if literal := _literals_var.get().get(target):
            return cls.simple(target, literal)

        a, b, c, d, e, f, g = (cls._decompose(n) for n in _decompose_int(abs(target)))

        if target > 0:
            option_1 = a**b * c + d
            option_2 = e**f + g
        else:
            if c.is_equation or c.value == 0:
                option_1 = -(a**b * c + d)
            else:
                option_1 = a**b * -c - d
            option_2 = -(e**f + g)

        return min(
            (option_1, len(option_1.patterns), sum(abs(n.value) for n in (a, b, c, d))),
            (option_2, len(option_2.patterns), sum(abs(n.value) for n in (e, f, g))),
            key=lambda v: (v[1], v[2]),
        )[0]

    @property
    def is_equation(self):
        return len(self.patterns) > 1

    def wrap_equation(self, if_add: bool = False) -> str:
        if len(self.patterns) == 1 or (if_add and "+" not in self.equation):
            return self.equation
        return f"({self.equation})"

    def simplify(self) -> DecomposedNumber:
        if self.value.is_integer():
            value = int(self.value)
            if literal := _literals_var.get().get(value):
                return DecomposedNumber.simple(value, literal)
        return self

    def __add__(self, other: DecomposedNumber) -> DecomposedNumber:
        if self.value == 0:
            return other
        if other.value == 0:
            return self
        return DecomposedNumber(
            value=self.value + other.value,
            equation=f"{self.equation} + {other.equation}",
            patterns=(*self.patterns, *other.patterns, ADD),
        ).simplify()

    def __sub__(self, other: DecomposedNumber) -> DecomposedNumber:
        if self.value == 0:
            return -other
        if other.value == 0:
            return self
        return DecomposedNumber(
            value=self.value - other.value,
            equation=f"{self.equation} - {other.equation}",
            patterns=(*self.patterns, *other.patterns, SUB),
        ).simplify()

    def __mul__(self, other: DecomposedNumber) -> DecomposedNumber:
        if self.value == 0 or other.value == 1:
            return self
        if other.value == 0 or self.value == 1:
            return other
        return DecomposedNumber(
            value=self.value * other.value,
            equation=f"{self.wrap_equation(if_add=True)} × {other.wrap_equation(if_add=True)}",
            patterns=(*self.patterns, *other.patterns, MUL),
        ).simplify()

    def __truediv__(self, other: DecomposedNumber) -> DecomposedNumber:
        if self.value == 0 or other.value == 1:
            return self
        return DecomposedNumber(
            value=self.value / other.value,
            equation=f"{self.wrap_equation()} ÷ {other.wrap_equation()}",
            patterns=(*self.patterns, *other.patterns, DIV),
        ).simplify()

    def __pow__(self, other: DecomposedNumber) -> DecomposedNumber:
        if other.value == 0:
            return DecomposedNumber.one()
        if self.value == 0 or self.value == 1 or other.value == 1:
            return self
        return DecomposedNumber(
            value=self.value**other.value,
            equation=f"{self.wrap_equation()}^{other.wrap_equation()}",
            patterns=(*self.patterns, *other.patterns, POW),
        ).simplify()

    def __neg__(self) -> DecomposedNumber:
        if self.is_equation:
            return self * DecomposedNumber.negative_one()
        if self.value < 0:
            pattern = HexPattern(
                HexDir.SOUTH_EAST, "aqaa" + self.patterns[0].signature[4:]
            )
        else:
            pattern = HexPattern(
                HexDir.NORTH_EAST, "dedd" + self.patterns[0].signature[4:]
            )
        return DecomposedNumber.simple(-self.value, pattern)


# algorithms by DaComputerNerd


def _decompose_int(num: int) -> tuple[int, int, int, int, int, int, int]:
    """Returns: a^b * c + d"""

    best_a = best_e = 2
    best_b, best_c, best_d, best_f, best_g = _decompose_int_inner(num, best_a)

    for a in range(3, math.floor(math.sqrt(num)) + 1):
        b, c, d, f, g = _decompose_int_inner(num, a)
        if d < best_d:
            best_a, best_b, best_c, best_d = a, b, c, d
        if g < best_g:
            best_e, best_f, best_g = a, f, g

    return best_a, best_b, best_c, best_d, best_e, best_f, best_g


def _decompose_int_inner(num: int, a: int):
    b = math.floor(math.log(num, a))
    a_pow_b: int = a**b
    c = num // a_pow_b
    d = num - a_pow_b * c
    g = num - a_pow_b
    return b, c, d, b, g
