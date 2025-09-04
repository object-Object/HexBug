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
        return "".join(node.value for node in self._iter_nodes(iota, 0, True))

    def pretty_print(self, iota: Iota, *, indent: str = " " * 4):
        return "\n".join(
            node.pretty_print(indent) for node in self._iter_nodes(iota, 0, False)
        )

    def _iter_nodes(self, iota: Iota, level: int, inline: bool) -> Iterator[Node]:
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
                yield Node(self._number(value), level)

            case VectorIota(x=x, y=y, z=z):
                yield Node(
                    f"({self._number(x)}, {self._number(y)}, {self._number(z)})",
                    level,
                )

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
                    if inline and i > 0:
                        yield Node(", ", level + 1)
                    yield from self._iter_nodes(child, level + 1, inline)
                yield Node("]", level)

            case MatrixIota(rows=m, columns=n) if m == 0 or n == 0:
                yield Node(f"[({m}, {n})]", level)

            case MatrixIota(rows=1, columns=n, data=data):
                yield Node(
                    f"[({m}, {n}) | {', '.join(self._number(v) for v in data[0])}]",
                    level,
                )

            case MatrixIota(rows=m, columns=n, data=data):
                yield Node(f"[({m}, {n}) |", level)

                if inline:
                    for i, row in enumerate(data):
                        if i > 0:
                            yield Node("; ", level + 1)
                        yield Node(", ".join(self._number(v) for v in row), level + 1)
                else:
                    widths = [0] * n
                    for row in data:
                        for j, value in enumerate(row):
                            widths[j] = max(widths[j], len(self._number(value)))

                    for row in data:
                        yield Node(
                            " ".join(
                                self._number(value).ljust(widths[j])
                                for j, value in enumerate(row)
                            ),
                            level + 1,
                        )

                yield Node("]", level)

    def _number(self, n: float):
        return f"{n:.4f}".rstrip("0").rstrip(".")


@dataclass
class Node:
    value: str
    level: int

    def pretty_print(self, indent: str):
        return self.level * indent + self.value
