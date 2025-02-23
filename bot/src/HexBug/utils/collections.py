from typing import Callable, Iterable, TypeVar

_T = TypeVar("_T")


def partition(
    values: Iterable[_T],
    predicate: Callable[[_T], bool],
) -> tuple[list[_T], list[_T]]:
    """Copies the contents of `values` into two lists based on a predicate.

    Returns: truthy, falsy
    """

    truthy = list[_T]()
    falsy = list[_T]()

    for value in values:
        if predicate(value):
            truthy.append(value)
        else:
            falsy.append(value)

    return truthy, falsy
