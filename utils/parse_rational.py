from decimal import Decimal, InvalidOperation
from fractions import Fraction


def parse_rational(number: str | float) -> Fraction | int | None:
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

    if dec.is_infinite() or dec.copy_abs() > 1_000_000_000_000:
        return None

    numerator, denominator = dec.as_integer_ratio()
    if denominator == 1:
        return numerator

    try:
        return Fraction(dec)
    except (ValueError, ZeroDivisionError, OverflowError):
        return None
