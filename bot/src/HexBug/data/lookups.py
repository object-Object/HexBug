from collections import defaultdict
from dataclasses import dataclass
from typing import Callable

from HexBug.core.exceptions import DuplicatePatternError

from .hex_math import HexAngle, HexPattern, HexSegment, align_segments_to_origin
from .patterns import PatternInfo


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

        self.segments = defaultdict[frozenset[HexSegment], list[PatternInfo]](list)
        self.per_world_segments = dict[frozenset[HexSegment], PatternInfo]()

    def add_pattern(self, pattern: PatternInfo):
        for lookup in [
            self.name,
            self.signature,
        ]:
            key = lookup.get_key(pattern)
            if (other := lookup.get(key)) and other is not pattern:
                raise DuplicatePatternError(lookup.name, key, pattern, other)
            lookup[key] = pattern

        segments = list(
            HexPattern(pattern.direction, pattern.signature).iter_segments()
        )
        for _ in range(6):
            segments = align_segments_to_origin(
                segment.rotated_by(HexAngle.RIGHT) for segment in segments
            )

            # TODO: refactor?
            if pattern.is_per_world:
                # per world patterns must not match the shape of ANY pattern
                if others := [
                    other for other in self.segments[segments] if other is not pattern
                ]:
                    # TODO: not a great error message
                    raise DuplicatePatternError(
                        "shape", "per world pattern", pattern, others[0]
                    )
                self.per_world_segments[segments] = pattern
            else:
                # normal patterns must not match the shape of any great spell
                # but they can match the shape of other patterns
                if (
                    other := self.per_world_segments.get(segments)
                ) and other is not pattern:
                    raise DuplicatePatternError(
                        "shape", "per world pattern", pattern, other
                    )

            self.segments[segments].append(pattern)
