"""
usage: python great_spells.py "pattern shorthand" [--symmetric]
"""

# pyright: reportInvalidTypeVarUse=false

import asyncio
import copy
import itertools
import sys
from contextlib import contextmanager
from multiprocessing import Lock, Pool, synchronize
from pathlib import Path
from typing import Any, Iterator, TypeVar

import networkx as nx
from aiohttp import ClientSession
from tqdm import tqdm

from HexBug.hexdecode.buildpatterns import build_registry
from HexBug.hexdecode.hex_math import Coord, Direction, get_pattern_segments
from HexBug.hexdecode.registry import NormalPatternInfo, RawPatternInfo, Registry, SpecialHandlerPatternInfo

T = TypeVar("T")


def pattern_to_graph(direction: Direction, pattern: str) -> nx.Graph:
    G = nx.Graph()

    for segment in get_pattern_segments(direction, pattern):
        G.add_edge(segment.root, segment.end)

    return G


def odd_degree_nodes(G: nx.Graph) -> Iterator[Any]:
    assert not isinstance(G.degree, int)

    for node, degree in G.degree:
        if degree % 2 != 0:
            yield node


def euler_start_points(G: nx.Graph) -> Iterator[Any]:
    odd = list(odd_degree_nodes(G))
    match len(odd):
        case 0:
            yield from G.nodes
        case 2:  # 2
            yield from odd
        case _:
            raise ValueError("Graph does not have an Eulerian path/circuit")


@contextmanager
def temporary_edge(G: nx.Graph, v: T, w: T) -> Iterator[None]:
    if G.has_edge(v, w):
        yield
    else:
        G.add_edge(v, w)
        yield
        G.remove_edge(v, w)


def non_isolated_view(G: nx.Graph):
    return nx.subgraph_view(G, filter_node=lambda n: not nx.is_isolate(G, n))


def has_euler_extension(G: nx.Graph, source: Any) -> bool:
    if not G.edges:
        return True
    if nx.is_isolate(G, source):
        return False
    return nx.has_eulerian_path(non_isolated_view(G), source)


def all_patterns(position: int, G: nx.Graph, v: Coord, direction: int) -> tuple[int, str, list[str]]:
    with lock:
        bar = tqdm(position=position, desc=f"{position:>2}", leave=False)

    patterns = list[str]()
    neighbors: list[Coord] = list(G[v])

    if direction >= len(neighbors):
        final_bar = str(bar)
        with lock:
            bar.close()
        return position, final_bar, []

    w = neighbors[direction]
    G.remove_edge(v, w)

    for path in all_euler_paths(G, w, [v, w]):
        pattern = points_to_pattern(path)
        patterns.append(pattern)

        with lock:
            bar.set_postfix_str(pattern)
            bar.update()

    final_bar = str(bar)
    with lock:
        bar.close()
    return position, final_bar, patterns


# https://stackoverflow.com/a/23543435
def all_euler_paths(G: nx.Graph, v: Coord, path: list[Coord]) -> Iterator[list[Coord]]:
    neighbors: list[Coord] = list(G[v])
    if not neighbors:
        yield path

    for w in neighbors:
        G.remove_edge(v, w)
        path.append(w)

        if has_euler_extension(G, w):
            yield from all_euler_paths(G, w, path)

        path.pop()
        G.add_edge(v, w)


def points_to_pattern(points: list[Coord]) -> str:
    compass = points[0].immediate_delta(points[1])
    assert compass

    pattern = ""

    for v, w in itertools.pairwise(points[1:]):
        next_compass = v.immediate_delta(w)
        assert next_compass
        pattern += next_compass.angle_from(compass).letter
        compass = next_compass

    return pattern


def init(l: synchronize.Lock):
    global lock
    lock = l


def get_name_and_pattern(registry: Registry, target: str) -> tuple[str, str]:
    match registry.from_shorthand(target):
        case NormalPatternInfo(display_name=name, pattern=pattern), _:
            return name, pattern
        case RawPatternInfo(pattern=pattern), _:
            return pattern, pattern
        case SpecialHandlerPatternInfo(display_name=name), _:
            raise ValueError(f"Pattern {name} (from {target}) does not have a predefined pattern")
        case None:
            pass

    if target in registry.from_pattern:
        info = registry.from_pattern[target]
        return info.display_name, target

    return target, target


async def _build_registry():
    async with ClientSession() as session:
        return await build_registry(session)


if __name__ == "__main__":
    registry = asyncio.run(_build_registry())
    assert registry

    name, target = get_name_and_pattern(registry, sys.argv[1])
    name = name.replace(" ", "_").replace("'", "")
    print(f"\nGenerating permutations for {name} ({target}).")

    # setup parallel args

    G = pattern_to_graph(Direction.EAST, target)
    starts = list(euler_start_points(G))

    if len(starts) == 2:
        # scuffed. but i don't feel like setting up argparse
        if sys.argv[2] == "--symmetric":
            print(f"Assuming symmetric.")
            starts = [starts[0]]

        args = [
            (i, copy.deepcopy(G), start, direction)
            for i, (start, direction) in enumerate((start, direction) for start in starts for direction in range(6))
        ]
    else:
        args = [(i, copy.deepcopy(G), start, i) for i, start in enumerate(starts)]

    # parallel processing

    print()
    with Pool(10, initializer=init, initargs=[Lock()]) as pool:
        results = pool.starmap(all_patterns, args)
    print()

    # output

    patterns = set[str]()
    for _, bar, result in sorted(results, key=lambda r: r[0]):
        patterns.update(result)
        if "0it [00:00, ?it/s]" not in bar:
            print(bar)

    print(f"\nTotal: {len(patterns)}\n")
    Path(f"great_spells/{name}.txt").write_text("\n".join(sorted(patterns)))

    # image, _ = draw_patterns_on_grid([(Direction.EAST, path) for path in paths], None, 5, Palette.Classic, Theme.Dark, 6, 2)
    # Path("test.png").write_bytes(image.getvalue())
