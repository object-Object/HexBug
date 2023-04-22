import math
from decimal import Decimal, InvalidOperation
from fractions import Fraction

from hexdecode.buildpatterns import MAX_PREGEN_NUMBER
from hexdecode.hex_math import Direction
from hexdecode.registry import Registry
from utils.patterns import align_horizontal

_ADDITIVE = (Direction.NORTH_EAST, "waaw")
_MULTIPLICATIVE = (Direction.SOUTH_EAST, "waqaw")
_DIVISION = (Direction.NORTH_EAST, "wdedw")
_POWER = (Direction.NORTH_WEST, "wedew")


def _decompose(target: int) -> tuple[int, int, int]:
    best_base, best_remainder = 0, target

    for base in range(2, math.floor(math.sqrt(target))):
        exponent = math.floor(math.log(target, base))
        remainder = target - base**exponent

        if remainder < best_remainder:
            best_base = base
            best_remainder = remainder

    return best_base, math.floor(math.log(target, best_base)), best_remainder


def _extend_patterns(
    registry: Registry,
    patterns: list[tuple[Direction, str]],
    math_ops: list[str],
    pattern_ops: list[str],
    target: int,
    paren: bool,
):
    if target > MAX_PREGEN_NUMBER:
        new_patterns, new_math_ops, new_pattern_ops = _recursive_generate_decomposed_number(registry, target)

        patterns.extend(new_patterns)
        pattern_ops.extend(new_pattern_ops)
        if paren:
            math_ops.extend(["("] + new_math_ops + [")"])
        else:
            math_ops.extend(new_math_ops)
    else:
        patterns.append(align_horizontal(*registry.pregen_numbers[target], True))
        pattern_ops.append(f"Numerical Reflection: {target}")
        math_ops.append(str(target))


def _recursive_generate_decomposed_number(
    registry: Registry, target: int
) -> tuple[list[tuple[Direction, str]], list[str], list[str]]:
    is_negative = target < 0
    target = abs(target)
    base, exponent, remainder = _decompose(target)

    patterns: list[tuple[Direction, str]] = []
    math_ops: list[str] = []
    pattern_ops: list[str] = []

    _extend_patterns(registry, patterns, math_ops, pattern_ops, base, True)
    math_ops.append("^")
    _extend_patterns(registry, patterns, math_ops, pattern_ops, exponent, True)
    patterns.append(_POWER)
    pattern_ops.append("Power Distillation")

    if remainder != 0:
        math_ops.append(" + ")
        _extend_patterns(registry, patterns, math_ops, pattern_ops, remainder, False)
        patterns.append(_ADDITIVE)
        pattern_ops.append("Additive Distillation")

    if is_negative:
        patterns.append(registry.pregen_numbers[-1])
        patterns.append(_MULTIPLICATIVE)
        pattern_ops.append("Multiplicative Distillation")
        math_ops.insert(0, "-(")
        math_ops.append(")")

    return patterns, math_ops, pattern_ops


def generate_decomposed_number(
    registry: Registry, target: Fraction | int, paren: bool = False
) -> tuple[list[tuple[Direction, str]], str, list[str]] | None:
    if isinstance(target, Fraction):
        numerator = generate_decomposed_number(registry, target.numerator, True)
        denominator = generate_decomposed_number(registry, target.denominator, True)

        if numerator is None or denominator is None:
            return None

        numerator_patterns, numerator_math_ops, numerator_pattern_ops = numerator
        denominator_patterns, denominator_math_ops, denominator_pattern_ops = denominator

        return (
            numerator_patterns + denominator_patterns + [_DIVISION],
            numerator_math_ops + " / " + denominator_math_ops,
            numerator_pattern_ops + denominator_pattern_ops,
        )

    else:
        if result := registry.pregen_numbers.get(target):
            return [align_horizontal(*result, True)], str(target), [f"Numerical Reflection: {target}"]

        try:
            patterns, math_ops, pattern_ops = _recursive_generate_decomposed_number(registry, target)
            if paren:
                math_ops = ["("] + math_ops + [")"]
            return patterns, "".join(math_ops), pattern_ops
        except ValueError:
            return None
