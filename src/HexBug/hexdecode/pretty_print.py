from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator

from .hexast import Iota, PatternIota
from .registry import NormalPatternInfo, Registry, SpecialHandlerPatternInfo


@dataclass
class IotaPrinter:
    registry: Registry | None = None

    def print(self, iota: Iota):
        return "".join(node.value for node in self._flatten(iota, 0))

    def pretty_print(self, iota: Iota, *, indent: str = " " * 4):
        return "\n".join(
            node.print(indent)
            for node in self._flatten(iota, 0)
            if not node.inline_only
        )

    def _flatten(self, iota: Iota, level: int) -> Iterator[Node]:
        match iota:
            case float() | int():
                yield Node(f"{iota:.4f}", level)

            case str():
                yield Node(f'"{iota}"', level)

            case PatternIota():
                yield Node(self._format_pattern(iota), level)

            case []:
                yield Node("[]", level)

            case [*children]:
                yield Node("[", level)
                for i, child in enumerate(children):
                    if i:
                        yield Node(", ", level + 1, inline_only=True)
                    yield from self._flatten(child, level + 1)
                yield Node("]", level)

            case _:
                yield Node(str(iota), level)

    def _format_pattern(self, iota: PatternIota):
        if self.registry:
            info = self.registry.parse_unknown_pattern(iota.direction, iota.pattern)
            match info:
                case NormalPatternInfo() | SpecialHandlerPatternInfo(value=None):
                    return info.display_name
                case SpecialHandlerPatternInfo():
                    return f"{info.display_name}: {info.value}"
                case _:
                    pass
        return str(iota)


@dataclass
class Node:
    value: str
    level: int
    inline_only: bool = False

    def print(self, indent: str):
        return self.level * indent + self.value
