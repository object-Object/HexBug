from typing import Callable, Iterable


def partition[T](
    values: Iterable[T],
    predicate: Callable[[T], bool],
) -> tuple[list[T], list[T]]:
    """Copies the contents of `values` into two lists based on a predicate.

    Returns: truthy, falsy
    """

    truthy = list[T]()
    falsy = list[T]()

    for value in values:
        if predicate(value):
            truthy.append(value)
        else:
            falsy.append(value)

    return truthy, falsy
