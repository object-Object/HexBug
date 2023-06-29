import asyncio
import atexit
import functools
import math
import sys
from concurrent import futures
from decimal import Decimal, InvalidOperation
from fractions import Fraction
from timeit import default_timer as timer

from hexnumgen import AStarOptions, GeneratedNumber, generate_number_pattern

from ..hexdecode.buildpatterns import MAX_PREGEN_NUMBER
from ..hexdecode.hex_math import Direction
from ..hexdecode.registry import Registry
from .patterns import align_horizontal

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
    align: bool,
    math_ops: list[str],
    pattern_ops: list[str],
    target: int,
    paren: bool,
):
    if target > MAX_PREGEN_NUMBER:
        new_patterns, new_math_ops, new_pattern_ops = _recursive_generate_decomposed_number(registry, target, align)

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
    registry: Registry,
    target: int,
    align: bool,
) -> tuple[list[tuple[Direction, str]], list[str], list[str]]:
    is_negative = target < 0
    target = abs(target)
    base, exponent, remainder = _decompose(target)

    patterns: list[tuple[Direction, str]] = []
    math_ops: list[str] = []
    pattern_ops: list[str] = []

    _extend_patterns(registry, patterns, align, math_ops, pattern_ops, target=base, paren=True)
    math_ops.append("^")
    _extend_patterns(registry, patterns, align, math_ops, pattern_ops, target=exponent, paren=True)
    patterns.append(_POWER)
    pattern_ops.append("Power Distillation")

    if remainder != 0:
        math_ops.append(" + ")
        _extend_patterns(registry, patterns, align, math_ops, pattern_ops, target=remainder, paren=False)
        patterns.append(_ADDITIVE)
        pattern_ops.append("Additive Distillation")

    if is_negative:
        patterns.append(registry.pregen_numbers[-1])
        patterns.append(_MULTIPLICATIVE)
        pattern_ops.append("Multiplicative Distillation")
        math_ops.insert(0, "-(")
        math_ops.append(")")

    return patterns, math_ops, pattern_ops


async def _timeout_generate_number_pattern(target: Fraction, timeout: float) -> tuple[Direction, str, float] | None:
    proc = await asyncio.create_subprocess_exec(
        sys.executable,
        "hexnumgen_cli.py",
        str(target.numerator),
        str(target.denominator),
        stdout=asyncio.subprocess.PIPE,
    )

    # kill the child if the parent dies (lol) (lmao)
    # there are issues with this: https://stackoverflow.com/a/14128476 (also SIGTERM, SIGKILL)
    # also there's a race condition if the bot dies between creating the process and registering this
    # but until these actually cause issues I'm not going to bother fixing them
    atexit.register(proc.kill)

    try:
        # get stdin data and wait up to timeout seconds for it to terminate itself
        start = timer()
        data, _ = await asyncio.wait_for(proc.communicate(), timeout)
        elapsed = timer() - start
    except asyncio.TimeoutError:
        # timed out, kill it with fire
        proc.kill()
        return
    finally:
        # always unregister the atexit kill function when done, even if we returned out
        atexit.unregister(proc.kill)

    if proc.returncode:
        # something went wrong
        return

    try:
        # extract the passed data
        direction, pattern = data.decode().strip().split(" ")
        return Direction[direction], pattern, elapsed
    except (ValueError, KeyError):
        # just in case
        return None


async def generate_decomposed_number(
    registry: Registry,
    target: Fraction | int,
    align: bool,
    paren: bool = False,
) -> tuple[list[tuple[Direction, str]], str, list[str]] | None:
    if isinstance(target, Fraction):
        if (result := await _timeout_generate_number_pattern(target, 1)) is not None:
            return (
                [align_horizontal(*result[:2], True) if align else result[:2]],
                f"{float(target)}\n\nA* finished in {result[2]:.2f} seconds.",
                [f"Numerical Reflection: {float(target)}"],
            )

        numerator = await generate_decomposed_number(registry, target.numerator, align, True)
        denominator = await generate_decomposed_number(registry, target.denominator, align, True)

        if numerator is None or denominator is None:
            return None

        numerator_patterns, numerator_math_ops, numerator_pattern_ops = numerator
        denominator_patterns, denominator_math_ops, denominator_pattern_ops = denominator

        return (
            numerator_patterns + denominator_patterns + [_DIVISION],
            f"{numerator_math_ops} / {denominator_math_ops}\n\nA* timed out, showing decomposition instead.",
            numerator_pattern_ops + denominator_pattern_ops,
        )

    else:
        if result := registry.pregen_numbers.get(target):
            return (
                [align_horizontal(*result, True) if align else result],
                str(target),
                [f"Numerical Reflection: {target}"],
            )

        try:
            patterns, math_ops, pattern_ops = _recursive_generate_decomposed_number(registry, target, align)
            if paren:
                math_ops = ["("] + math_ops + [")"]
            return patterns, "".join(math_ops), pattern_ops
        except ValueError:
            return None
