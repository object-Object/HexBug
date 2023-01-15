from decimal import Decimal, InvalidOperation
from fractions import Fraction

_MAX_NUMBER = 1_000_000_000_000
_MAX_LENGTH = 4 * len(str(_MAX_NUMBER))


def _parse_rational(number: str | float) -> Fraction | int | None:
    try:
        dec = Decimal(number)
    except InvalidOperation:
        dec = None

    if dec is None:
        try:
            frac = Fraction(number)
        except (ValueError, ZeroDivisionError):
            return None
        else:
            if frac.denominator == 1:
                return frac.numerator
            return frac

    if dec.is_infinite():
        return None

    numerator, denominator = dec.as_integer_ratio()
    if denominator == 1:
        return numerator

    try:
        return Fraction(dec)
    except (ValueError, ZeroDivisionError, OverflowError):
        return None


def parse_rational(number: str | float) -> Fraction | int | None:
    if len(str(number)) > _MAX_LENGTH:
        return None

    match rational := _parse_rational(number):
        case Fraction():
            if abs(rational.numerator) > _MAX_NUMBER or abs(rational.denominator) > _MAX_NUMBER:
                return None
        case int():
            if abs(rational) > _MAX_NUMBER:
                return None

    return rational
