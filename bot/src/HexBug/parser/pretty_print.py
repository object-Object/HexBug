from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from typing import Iterator

from HexBug.data import static_data
from HexBug.data.patterns import PatternInfo
from HexBug.data.registry import HexBugRegistry

from .ast import (
    BooleanIota,
    BubbleIota,
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
    _level: int
    _min_level: int

    def __init__(self, registry: HexBugRegistry):
        self.registry = registry
        self._level = 0
        self._min_level = 0

    def print(self, iota: Iota):
        with self._reset():
            return "".join(node.value for node in self._iter_nodes(iota, inline=True))

    def pretty_print(
        self,
        iota: Iota,
        *,
        indent: str = " " * 4,
        flatten_list: bool = False,
    ):
        with self._reset():
            if flatten_list and isinstance(iota, ListIota):
                nodes = (
                    node
                    for inner in iota.values
                    for node in self._iter_embedded_nodes(inner, inline=False)
                )
            else:
                nodes = self._iter_nodes(iota, inline=False)

            return "\n".join(node.pretty_print(indent) for node in nodes)

    def _iter_embedded_nodes(self, iota: Iota, inline: bool) -> Iterator[Node]:
        nodes = self._iter_nodes(iota, inline)
        if isinstance(iota, PatternIota):
            yield from nodes
            return

        match list(nodes):
            case [node]:
                yield "<" + node + ">"
            case [first, *middle, last]:
                yield "<" + first
                yield from middle
                yield last + ">"
            case other:
                yield from other

    def _iter_nodes(self, iota: Iota, inline: bool) -> Iterator[Node]:
        match iota:
            case PatternIota(direction=direction, signature=signature):
                match self.registry.try_match_pattern(direction, signature):
                    case PatternInfo(id=static_data.INTROSPECTION) if not inline:
                        yield self._node("{")
                        self._level += 1
                    case PatternInfo(id=static_data.RETROSPECTION) if not inline:
                        self._level -= 1
                        yield self._node("}")
                    case None:
                        signature = (" " + signature) if signature else ""
                        yield self._node(f"HexPattern({direction.name}{signature})")
                    case match:
                        yield self._node(match.name)

            case BubbleIota(inner=inner):
                yield self._node("{" + self.print(inner) + "}")

            case JumpIota():
                yield self._node("[Jump]")

            case CallIota():
                yield self._node("[Call]")

            case NumberIota(value=value):
                yield self._node(self._number(value))

            case VectorIota(x=x, y=y, z=z):
                yield self._node(
                    f"({self._number(x)}, {self._number(y)}, {self._number(z)})"
                )

            case BooleanIota(value=value):
                yield self._node(str(value))

            case NullIota():
                yield self._node("Null")

            case StringIota(value=value):
                yield self._node(f'"{value}"')

            case UnknownIota(value=value):
                yield self._node(value)

            case ListIota([]):
                yield self._node("[]")

            case ListIota([*children]):
                yield self._node("[")
                with self._indent(), self._set_min_level():
                    for i, child in enumerate(children):
                        if inline and i > 0:
                            yield self._node(", ")
                        yield from self._iter_nodes(child, inline)
                yield self._node("]")

            case MatrixIota(rows=m, columns=n) if m == 0 or n == 0:
                yield self._node(f"[({m}, {n})]")

            case MatrixIota(rows=1, columns=n, data=data):
                yield self._node(
                    f"[({1}, {n}) | {', '.join(self._number(v) for v in data[0])}]"
                )

            case MatrixIota(rows=m, columns=n, data=data):
                yield self._node(f"[({m}, {n}) |")

                if inline:
                    for i, row in enumerate(data):
                        if i > 0:
                            yield self._node("; ")
                        yield self._node(", ".join(self._number(v) for v in row))
                else:
                    widths = [0] * n
                    for row in data:
                        for j, value in enumerate(row):
                            widths[j] = max(widths[j], len(self._number(value)))

                    with self._indent():
                        for row in data:
                            yield self._node(
                                " ".join(
                                    self._number(value).ljust(widths[j])
                                    for j, value in enumerate(row)
                                )
                            )

                yield self._node("]")

    def _number(self, n: float):
        return f"{n:.4f}".rstrip("0").rstrip(".")

    @property
    def _safe_level(self):
        return max(self._level, self._min_level)

    def _node(self, value: str):
        return Node(value, self._safe_level)

    @contextmanager
    def _reset(self):
        prev = (self._level, self._min_level)
        self._level = 0
        self._min_level = 0
        yield
        self._level, self._min_level = prev

    @contextmanager
    def _indent(self, amount: int = 1):
        prev = self._level
        self._level = self._safe_level + amount
        yield
        self._level = prev

    @contextmanager
    def _set_min_level(self):
        prev = self._min_level
        self._min_level = self._safe_level
        yield
        self._level = self._min_level = prev


@dataclass
class Node:
    value: str
    level: int

    def pretty_print(self, indent: str):
        return self.level * indent + self.value

    def __add__(self, other: str):
        return Node(self.value + other, self.level)

    def __radd__(self, other: str):
        return Node(other + self.value, self.level)
