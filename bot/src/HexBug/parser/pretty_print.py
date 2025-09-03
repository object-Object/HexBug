from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator

from HexBug.data.registry import HexBugRegistry

from .ast import (
    BooleanIota,
    CallIota,
    Iota,
    JumpIota,
    ListIota,
    MatrixIota,
    NullIota,
    NumberIota,
    PatternIota,
    StringIota,
    UnknownIota,
    VectorIota,
)


class IotaPrinter:
    registry: HexBugRegistry

    def __init__(self, registry: HexBugRegistry):
        self.registry = registry

    def print(self, iota: Iota):
        return "".join(node.value for node in self._iter_nodes(iota, 0))

    def pretty_print(self, iota: Iota, *, indent: str = " " * 4):
        return "\n".join(
            node.pretty_print(indent)
            for node in self._iter_nodes(iota, 0)
            if not node.inline
        )

    def _iter_nodes(self, iota: Iota, level: int) -> Iterator[Node]:
        match iota:
            case PatternIota(direction=direction, signature=signature):
                if match := self.registry.try_match_pattern(direction, signature):
                    value = match.name
                else:
                    signature = (" " + signature) if signature else ""
                    value = f"HexPattern({direction.name}{signature})"
                yield Node(value, level)

            case JumpIota():
                yield Node("[Jump]", level)

            case CallIota():
                yield Node("[Call]", level)

            case NumberIota(value=value):
                yield Node(f"{value:.4f}", level)

            case VectorIota(x=x, y=y, z=z):
                yield Node(f"({x:.4f}, {y:.4f}, {z:.4f})", level)

            case BooleanIota(value=value):
                yield Node(str(value), level)

            case NullIota():
                yield Node("Null", level)

            case StringIota(value=value):
                yield Node(f'"{value}"', level)

            case UnknownIota(value=value):
                yield Node(value, level)

            case ListIota([]):
                yield Node("[]", level)

            case ListIota([*children]):
                yield Node("[", level)
                for i, child in enumerate(children):
                    if i > 0:
                        yield Node(", ", level + 1, inline=True)
                    yield from self._iter_nodes(child, level + 1)
                yield Node("]", level)

            case MatrixIota(rows=m, columns=n) if m == 0 or n == 0:
                yield Node(f"[({m}, {n})]", level)

            case MatrixIota(rows=1, columns=n, data=data):
                yield Node(
                    f"[({m}, {n}) | {', '.join(str(n) for n in data[0])}]", level
                )

            case MatrixIota(rows=m, columns=n, data=data):
                yield Node(f"[({m}, {n}) |", level)
                for i, row in enumerate(data):
                    semicolon = ";" if i + 1 < len(data) else ""
                    yield Node(", ".join(str(n) for n in row) + semicolon, level + 1)
                yield Node("]", level)


@dataclass
class Node:
    value: str
    level: int
    inline: bool = False

    def pretty_print(self, indent: str):
        return self.level * indent + self.value
