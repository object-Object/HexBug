from typing import Callable, Iterable

from hexdoc.core import ResourceLocation
from ordered_set import OrderedSet


class ResourceSet:
    """A set of ResourceLocations that allows matching both by hash and by pattern."""

    def __init__(
        self,
        values: Iterable[ResourceLocation] = [],
        patterns: Iterable[ResourceLocation] = [],
    ):
        self._values = set(values)
        self._patterns = OrderedSet(patterns)

    def add(self, value: ResourceLocation):
        self._values.add(value)

    def add_pattern(self, pattern: ResourceLocation):
        self._patterns.add(pattern)

    def __contains__(self, value: ResourceLocation) -> bool:
        if value in self._values:
            return True
        for pattern in self._patterns:
            if value.match(pattern):
                return True
        return False


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
