from dataclasses import dataclass
from typing import Callable

from HexBug.core.exceptions import DuplicatePatternError
from HexBug.data.patterns import PatternInfo


@dataclass
class PatternLookup[K](dict[K, PatternInfo]):
    name: str
    get_key: Callable[[PatternInfo], K]

    def __post_init__(self):
        super().__init__()


class PatternLookups:
    def __init__(self):
        self.name = PatternLookup("name", lambda p: p.name)
        self.signature = PatternLookup("signature", lambda p: p.signature)

    def add_pattern(self, pattern: PatternInfo):
        for lookup in [self.name, self.signature]:
            key = lookup.get_key(pattern)
            if (other := lookup.get(key)) and other is not pattern:
                raise DuplicatePatternError(lookup.name, key, pattern, other)
            lookup[key] = pattern
