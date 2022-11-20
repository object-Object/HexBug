"""
MIT License

Copyright (c) 2022 Graham Hughes, object-Object

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

https://github.com/gchpaco/hexdecode
"""

import re
from pathlib import Path

from Hexal.doc.collate_data import parse_book as hexal_parse_book
from hexdecode.hexast import (
    Book,
    BookEntry,
    BookPage_hexcasting_manual_pattern,
    BookPage_hexcasting_pattern,
    BookPage_patchouli_spotlight,
    BookPage_patchouli_text,
    Direction,
    ModName,
    Registry,
    get_rotated_pattern_segments,
    isbookpage,
)
from HexMod.doc.collate_data import parse_book as hex_parse_book

# thanks Alwinfy for (unknowingly) making my registry regex about 5x simpler
registry_regex = re.compile(
    r'HexPattern\.fromAngles\("([qweasd]+)", HexDir\.(\w+)\),\s*modLoc\("([^"]+)"\)[^;]+?(Operator|Op\w+|Widget)([^;]*true\);)?',
    re.M,
)
# thanks Talia for changing the registry format
hexal_registry_regex = re.compile(
    r'HexPattern\.fromAngles\("([qweasd]+)", HexDir\.(\w+)\),\s*modLoc\("([^"]+)"\)[^val]+?(Operator|Op\w+|Widget)(?:[^val]*[^\(](true)\))?',
    re.M,
)
translation_regex = re.compile(r"hexcasting.spell.[a-z]+:(.+)")
header_regex = re.compile(r"\s*\(.+\)")

pattern_files: list[tuple[ModName, str]] = [
    ("Hex Casting", "HexMod/Common/src/main/java/at/petrak/hexcasting/common/casting/RegisterPatterns.java"),
    ("Hex Casting", "HexMod/Common/src/main/java/at/petrak/hexcasting/interop/pehkui/PehkuiInterop.java"),
    ("Hex Casting", "HexMod/Fabric/src/main/java/at/petrak/hexcasting/fabric/interop/gravity/GravityApiInterop.java"),
    ("Hexal", "Hexal/Common/src/main/java/ram/talia/hexal/common/casting/Patterns.kt"),
]

operator_directories: list[tuple[ModName, str]] = [
    ("Hex Casting", "HexMod/Common/src/main/java/at/petrak/hexcasting/common/casting/operators"),
    ("Hex Casting", "HexMod/Common/src/main/java/at/petrak/hexcasting/interop/pehkui"),
    ("Hex Casting", "HexMod/Fabric/src/main/java/at/petrak/hexcasting/fabric/interop/gravity"),
    ("Hexal", "Hexal/Common/src/main/java/ram/talia/hexal/common/casting/actions"),
]


def _build_pattern_urls(
    registry: Registry,
    entry: BookEntry,
    page: BookPage_hexcasting_pattern | BookPage_hexcasting_manual_pattern,
    mod: ModName,
):
    if "anchor" not in page:
        return None

    inp = f"__{inp}__" if (inp := page.get("input")) else ""
    oup = f"__{oup}__" if (oup := page.get("output")) else ""
    args = f"**{f'{inp} → {oup}'.strip()}**" if inp or oup else None

    url = f"#{entry['id']}@{page['anchor']}"
    names: set[str] = set()
    names.add(page["op_id"].split(":", 1)[1])

    for pattern, _, _ in page["op"]:  # pretty sure this only catches the vector reflections right now
        if name := registry.pattern_to_name.get(pattern):
            names.add(name)

    for name in names:
        registry.name_to_url[name] = (mod, url)
        if args:
            registry.name_to_args[name] = args

    return (mod, url, list(names))


def _build_urls(registry: Registry, book: Book, mod: ModName):
    for category in book["categories"]:
        registry.page_title_to_url[category["name"]] = (mod, f"#{category['id']}", [])

        for entry in category["entries"]:
            registry.page_title_to_url[entry["name"]] = (mod, f"#{entry['id']}", [])

            for page in entry["pages"]:
                if isbookpage(page, BookPage_patchouli_text) and "title" in page and "anchor" in page:
                    registry.page_title_to_url[page["title"]] = (mod, f"#{entry['id']}@{page['anchor']}", [])

                elif isbookpage(page, BookPage_patchouli_spotlight) and "anchor" in page:
                    registry.page_title_to_url[page["item_name"]] = (mod, f"#{entry['id']}@{page['anchor']}", [])

                elif isbookpage(page, BookPage_hexcasting_pattern) and (
                    value := _build_pattern_urls(registry, entry, page, mod)
                ):
                    registry.page_title_to_url[page["name"]] = value

                elif isbookpage(page, BookPage_hexcasting_manual_pattern) and (
                    value := _build_pattern_urls(registry, entry, page, mod)
                ):
                    registry.page_title_to_url[header_regex.sub("", page["header"])] = value


def build_registry() -> Registry:
    registry = Registry()
    hex_book: Book = hex_parse_book("HexMod/Common/src/main/resources", "hexcasting", "thehexbook")
    hexal_book: Book = hexal_parse_book(
        "Hexal/Common/src/main/resources", "Hexal/doc/HexCastingResources", "hexal", "hexalbook"
    )

    # translations
    for key, translation in dict(hex_book["i18n"], **hexal_book["i18n"]).items():
        if match := translation_regex.match(key):
            name = match[1]
            # because the new built in decoding interferes with this
            registry.name_to_translation[name] = translation.replace(": %s", "")

    # get classname_to_path
    classname_to_path: dict[str, str] = {
        "Operator": "Common/src/main/java/at/petrak/hexcasting/api/spell/Operator.kt",
        "Widget": "Common/src/main/java/at/petrak/hexcasting/api/spell/Widget.kt",
    }
    for mod, directory in operator_directories:
        for path in Path(directory).rglob("Op*.kt"):
            path = path.relative_to(path.parts[0])
            key = path.stem
            if duplicate := classname_to_path.get(key):  # this *should* never happen
                raise Exception(f"Duplicate classname: {key} ({path} and {duplicate})")
            classname_to_path[key] = path.as_posix()

    # patterns - can't use the Book data here because we also need the class name :pensivewobble:
    registry.translation_to_path["Bookkeeper's Gambit"] = (
        "Hex Casting",
        "Common/src/main/java/at/petrak/hexcasting/common/casting/RegisterPatterns.java",
        "mask",
    )
    registry.translation_to_path["Numerical Reflection"] = (
        "Hex Casting",
        "Common/src/main/java/at/petrak/hexcasting/common/casting/RegisterPatterns.java",
        "number",
    )
    for mod, filename in pattern_files:
        current_regex = hexal_registry_regex if mod == "Hexal" else registry_regex
        with open(filename, "r", encoding="utf-8") as file:
            for match in current_regex.finditer(file.read()):
                (pattern, direction, name, classname, is_great) = match.groups()
                if is_great:
                    for segments in get_rotated_pattern_segments(Direction[direction], pattern):
                        registry.great_spells[segments] = name
                else:
                    registry.pattern_to_name[pattern] = name
                # because Hexal sometimes doesn't have translations
                translation = registry.name_to_translation.get(name, name)
                registry.translation_to_pattern[translation] = (Direction[direction], pattern, bool(is_great), name)
                registry.translation_to_path[translation] = (mod, classname_to_path[classname], name)

    # books
    _build_urls(registry, hex_book, "Hex Casting")
    _build_urls(registry, hexal_book, "Hexal")

    return registry
