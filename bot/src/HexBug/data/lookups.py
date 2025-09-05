from collections import defaultdict
from dataclasses import dataclass
from typing import Callable

from HexBug.core.exceptions import DuplicatePatternError

from .hex_math import HexAngle, HexPattern, HexSegment, align_segments_to_origin
from .patterns import PatternInfo
from .special_handlers import SpecialHandlerInfo


@dataclass
class PatternLookup[K](dict[K, PatternInfo]):
    name: str
    get_key: Callable[[PatternInfo], K]

    def __post_init__(self):
        super().__init__()

    def add_or_raise(self, pattern: PatternInfo):
        key = self.get_key(pattern)
        if (other := self.get(key)) and other is not pattern:
            raise DuplicatePatternError(self.name, key, pattern.id, other.id)
        self[key] = pattern


@dataclass
class SpecialHandlerLookup[K](dict[K, SpecialHandlerInfo]):
    name: str
    get_key: Callable[[SpecialHandlerInfo], K]

    def __post_init__(self):
        super().__init__()


class PatternLookups:
    def __init__(self):
        self.name = PatternLookup("name", lambda p: p.name)
        self.signature = PatternLookup("signature", lambda p: p.signature)

        self.segments = defaultdict[frozenset[HexSegment], list[PatternInfo]](list)
        self.per_world_segments = dict[frozenset[HexSegment], PatternInfo]()

        self.special_handler_name = SpecialHandlerLookup("name", lambda i: i.base_name)

    def add_pattern(self, pattern: PatternInfo):
        if not pattern.is_hidden:
            self.name.add_or_raise(pattern)

        if not pattern.display_only:
            self.signature.add_or_raise(pattern)

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
                        other
                        for other in self.segments[segments]
                        if other is not pattern
                    ]:
                        # TODO: not a great error message
                        raise DuplicatePatternError(
                            "shape", "per world pattern", pattern.id, others[0].id
                        )
                    self.per_world_segments[segments] = pattern
                else:
                    # normal patterns must not match the shape of any great spell
                    # but they can match the shape of other patterns
                    if (
                        other := self.per_world_segments.get(segments)
                    ) and other is not pattern:
                        raise DuplicatePatternError(
                            "shape", "per world pattern", pattern.id, other.id
                        )

                self.segments[segments].append(pattern)

    def add_special_handler(self, info: SpecialHandlerInfo):
        for lookup in [
            self.special_handler_name,
        ]:
            key = lookup.get_key(info)
            if (other := lookup.get(key)) and other is not info:
                raise DuplicatePatternError(lookup.name, key, info.id, other.id)
            lookup[key] = info
