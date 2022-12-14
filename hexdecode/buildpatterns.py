import logging
import re
from pathlib import Path
from typing import TypeVar

from Hexal.doc.collate_data import parse_book as hexal_parse_book
from hexdecode.hexast import Direction, ModName, Registry, get_rotated_pattern_segments
from HexMod.doc.collate_data import parse_book as hex_parse_book
from MoreIotas.doc.collate_data import parse_book as moreiotas_parse_book
from utils.book_types import (
    Book,
    BookEntry,
    BookPage_hexcasting_manual_pattern,
    BookPage_hexcasting_pattern,
    BookPage_patchouli_spotlight,
    BookPage_patchouli_text,
)
from utils.book_utils import isbookpage
from utils.mods import MOD_INFO

# thanks Alwinfy for (unknowingly) making my registry regex about 5x simpler
registry_regex = re.compile(
    r'HexPattern\.fromAngles\("([qweasd]+)", HexDir\.(\w+)\),\s*modLoc\("([^"]+)"\)[^;]+?(makeConstantOp|Op\w+)([^;]*true\);)?',
    re.M,
)
# thanks Talia for changing the registry format
talia_registry_regex = re.compile(
    r'HexPattern\.fromAngles\("([qweasd]+)", HexDir\.(\w+)\),\s*modLoc\("([^"]+)"\)[^val]+?(makeConstantOp|Op\w+)(?:[^val]*[^\(](true)\))?',
    re.M,
)
translation_regex = re.compile(r"hexcasting.spell.[a-z]+:(.+)")
header_regex = re.compile(r"\s*\(.+\)")

pattern_files: list[tuple[ModName, str]] = [
    ("Hex Casting", "HexMod/Common/src/main/java/at/petrak/hexcasting/common/casting/RegisterPatterns.java"),
    ("Hex Casting", "HexMod/Common/src/main/java/at/petrak/hexcasting/interop/pehkui/PehkuiInterop.java"),
    ("Hex Casting", "HexMod/Fabric/src/main/java/at/petrak/hexcasting/fabric/interop/gravity/GravityApiInterop.java"),
    ("Hexal", "Hexal/Common/src/main/java/ram/talia/hexal/common/casting/Patterns.kt"),
    ("MoreIotas", "MoreIotas/Common/src/main/java/ram/talia/moreiotas/common/casting/Patterns.kt"),
]

operator_directories: list[tuple[ModName, str]] = [
    ("Hex Casting", "HexMod/Common/src/main/java/at/petrak/hexcasting/common/casting/operators"),
    ("Hex Casting", "HexMod/Common/src/main/java/at/petrak/hexcasting/interop/pehkui"),
    ("Hex Casting", "HexMod/Fabric/src/main/java/at/petrak/hexcasting/fabric/interop/gravity"),
    ("Hexal", "Hexal/Common/src/main/java/ram/talia/hexal/common/casting/actions"),
    ("MoreIotas", "MoreIotas/Common/src/main/java/ram/talia/moreiotas/common/casting/actions"),
]

# https://github.com/gamma-delta/HexMod/blob/main/Common/src/main/java/at/petrak/hexcasting/api/spell/casting/SpecialPatterns.java
# https://github.com/gamma-delta/HexMod/blob/main/Common/src/main/java/at/petrak/hexcasting/api/utils/PatternNameHelper.java
# (mod, pattern, direction, name, classname, is_great)
special_patterns: list[tuple[str, Direction, str, str, bool]] = [
    ("qqq", Direction.WEST, "open_paren", "INTROSPECTION", False),
    ("eee", Direction.EAST, "close_paren", "RETROSPECTION", False),
    ("qqqaw", Direction.WEST, "escape", "CONSIDERATION", False),
]


class DuplicatePatternException(Exception):
    def __init__(self, name1: str, name2: str, pattern: str, is_great: bool) -> None:
        super().__init__(f"Duplicate {'great spell' if is_great else 'pattern'} ({name1}, {name2}): {pattern}")


def _build_pattern_urls(
    registry: Registry,
    entry: BookEntry,
    page: BookPage_hexcasting_pattern | BookPage_hexcasting_manual_pattern,
    mod: ModName,
):
    inp = f"__{inp}__" if (inp := page.get("input")) else ""
    oup = f"__{oup}__" if (oup := page.get("output")) else ""
    args = f"**{f'{inp} → {oup}'.strip()}**" if inp or oup else None

    url = f"#{entry['id']}@{page['anchor']}" if "anchor" in page else None
    names: set[str] = set()
    if "op_id" in page:
        names.add(page["op_id"].split(":", 1)[1])

    for pattern, _, _ in page["op"]:  # pretty sure this only catches the vector reflections right now
        if name := registry.pattern_to_name.get(pattern):
            names.add(name)

    for name in names:
        registry.name_to_url[name] = (mod, url)
        if args:
            registry.name_to_args[name] = args

    if url is None:
        return None
    return (url, list(names))


def _build_urls(registry: Registry, book: Book, mod: ModName):
    for category in book["categories"]:
        registry.page_title_to_url[mod][category["name"]] = (f"#{category['id']}", [])

        for entry in category["entries"]:
            registry.page_title_to_url[mod][entry["name"]] = (f"#{entry['id']}", [])

            for page in entry["pages"]:
                if isbookpage(page, BookPage_patchouli_text) and "title" in page and "anchor" in page:
                    registry.page_title_to_url[mod][page["title"]] = (f"#{entry['id']}@{page['anchor']}", [])

                elif isbookpage(page, BookPage_patchouli_spotlight) and "anchor" in page:
                    registry.page_title_to_url[mod][page["item_name"]] = (f"#{entry['id']}@{page['anchor']}", [])

                elif isbookpage(page, BookPage_hexcasting_pattern) and (
                    value := _build_pattern_urls(registry, entry, page, mod)
                ):
                    registry.page_title_to_url[mod][page["name"]] = value

                elif isbookpage(page, BookPage_hexcasting_manual_pattern) and (
                    value := _build_pattern_urls(registry, entry, page, mod)
                ):
                    registry.page_title_to_url[mod][header_regex.sub("", page["header"])] = value


T = TypeVar("T")


def _check_duplicate(lookup: dict[T, str], key: T, name: str, pattern: str, is_great: bool):
    if (existing_name := lookup.get(key)) and existing_name != name:
        raise DuplicatePatternException(name, existing_name, pattern, is_great)


def _add_to_registry(
    registry: Registry,
    classname_to_path: dict[str, tuple[ModName, str]],
    pattern: str,
    direction: Direction,
    name: str,
    classname: str,
    is_great: bool,
) -> None:
    if is_great:
        for segments in get_rotated_pattern_segments(direction, pattern):
            _check_duplicate(
                lookup=registry.great_spells,
                key=segments,
                name=name,
                pattern=pattern,
                is_great=is_great,
            )
            registry.great_spells[segments] = name
    else:
        _check_duplicate(
            lookup=registry.pattern_to_name,
            key=pattern,
            name=name,
            pattern=pattern,
            is_great=is_great,
        )
        registry.pattern_to_name[pattern] = name
    # because Hexal sometimes doesn't have translations
    translation = registry.name_to_translation.get(name, name)
    registry.translation_to_pattern[translation] = (direction, pattern, is_great, name)
    registry.translation_to_path[translation] = (*classname_to_path[classname], name)


def merge_dicts(*dicts: dict[str, str]) -> dict[str, str]:
    output: dict[str, str] = {}
    for d in dicts:
        for key, value in d.items():
            if key not in output:
                output[key] = value
    return output


def build_registry() -> Registry:
    logging.log(logging.INFO, "building registry")
    registry = Registry(
        translation_to_path={
            "Numerical Reflection": (
                "Hex Casting",
                f"Common/src/main/java/at/petrak/hexcasting/common/casting/RegisterPatterns.java",
                "number",
            ),
            "Bookkeeper's Gambit": (
                "Hex Casting",
                f"Common/src/main/java/at/petrak/hexcasting/common/casting/RegisterPatterns.java",
                "mask",
            ),
        }
    )
    hex_book: Book = hex_parse_book("HexMod/Common/src/main/resources", "hexcasting", "thehexbook")
    hexal_book: Book = hexal_parse_book(
        "Hexal/Common/src/main/resources", "Hexal/doc/HexCastingResources", "hexal", "hexalbook"
    )
    moreiotas_book: Book = moreiotas_parse_book(
        "MoreIotas/Common/src/main/resources", "MoreIotas/doc/HexCastingResources", "moreiotas", "moreiotasbook"
    )

    # translations
    for key, translation in merge_dicts(hex_book["i18n"], hexal_book["i18n"], moreiotas_book["i18n"]).items():
        if match := translation_regex.match(key):
            name = match[1]
            # because the new built in decoding interferes with this
            registry.name_to_translation[name] = translation.replace(": %s", "")

    # get classname_to_path
    classname_to_path: dict[str, tuple[ModName, str]] = {
        "makeConstantOp": ("Hex Casting", f"Common/src/main/java/at/petrak/hexcasting/api/spell/Action.kt"),
        "CONSIDERATION": (
            "Hex Casting",
            f"Common/src/main/java/at/petrak/hexcasting/api/spell/casting/CastingHarness.kt",
        ),
        "INTROSPECTION": (
            "Hex Casting",
            f"Common/src/main/java/at/petrak/hexcasting/api/spell/casting/CastingHarness.kt",
        ),
        "RETROSPECTION": (
            "Hex Casting",
            f"Common/src/main/java/at/petrak/hexcasting/api/spell/casting/CastingHarness.kt",
        ),
    }
    for mod, directory in operator_directories:
        for path in Path(directory).rglob("Op*.kt"):
            final_path = path.relative_to(path.parts[0])
            key = final_path.stem
            if duplicate := classname_to_path.get(key):  # this *should* never happen
                raise Exception(f"Duplicate classname: {key} ({final_path} and {duplicate})")
            classname_to_path[key] = (mod, final_path.as_posix())

    # patterns - can't use the Book data here because we also need the class name :pensivewobble:
    for mod, filename in pattern_files:
        current_regex = talia_registry_regex if MOD_INFO[mod].uses_talia_registry else registry_regex
        with open(filename, "r", encoding="utf-8") as file:
            for match in current_regex.finditer(file.read()):
                (pattern, direction, name, classname, is_great) = match.groups()
                _add_to_registry(
                    registry, classname_to_path, pattern, Direction[direction], name, classname, bool(is_great)
                )

    for info in special_patterns:
        _add_to_registry(registry, classname_to_path, *info)

    # books
    _build_urls(registry, hex_book, "Hex Casting")
    _build_urls(registry, hexal_book, "Hexal")
    _build_urls(registry, moreiotas_book, "MoreIotas")

    return registry
