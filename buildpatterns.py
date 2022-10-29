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
from hexast import (BookEntry, Direction, get_rotated_pattern_segments, Registry, Book, BookPage_patchouli_text,
                    BookPage_patchouli_spotlight, BookPage_hexcasting_pattern, BookPage_hexcasting_manual_pattern, isbookpage)
from HexMod.doc.collate_data import parse_book as hex_parse_book
from Hexal.doc.collate_data import parse_book as hexal_parse_book

HEX_BASE_URL = "https://gamma-delta.github.io/HexMod/"
HEXAL_BASE_URL = "https://talia-12.github.io/Hexal/"

translation_regex = re.compile(r"hexcasting.spell.[a-z]+:(.+)")
header_regex = re.compile(r"\s*\(.+\)")

def _build_pattern_urls(
    registry: Registry,
    entry: BookEntry,
    page: BookPage_hexcasting_pattern | BookPage_hexcasting_manual_pattern,
    base_url: str
):
    if "anchor" not in page:
        return None

    inp = f"__{inp}__" if (inp := page.get("input")) else ""
    oup = f"__{oup}__" if (oup := page.get("output")) else ""
    args = f"**{f'{inp} → {oup}'.strip()}**" if inp or oup else None

    url = f"{base_url}#{entry['id']}@{page['anchor']}"
    names: set[str] = set()
    names.add(page["op_id"].split(":", 1)[1])

    for pattern, _, _ in page["op"]: # pretty sure this only catches the vector reflections right now
        if name := registry.pattern_to_name.get(pattern):
            names.add(name)

    for name in names:
        registry.name_to_url[name] = url
        if args:
            registry.name_to_args[name] = args

    return url

def _build_urls(registry: Registry, book: Book, base_url: str):
    for category in book["categories"]:
        registry.page_title_to_url[category["name"]] = f"{base_url}#{category['id']}"

        for entry in category["entries"]:
            registry.page_title_to_url[entry["name"]] = f"{base_url}#{entry['id']}"

            for page in entry["pages"]:
                if isbookpage(page, BookPage_patchouli_text) and "title" in page and "anchor" in page:
                    registry.page_title_to_url[page["title"]] = f"{base_url}#{entry['id']}@{page['anchor']}"

                elif isbookpage(page, BookPage_patchouli_spotlight) and "anchor" in page:
                    registry.page_title_to_url[page["item_name"]] = f"{base_url}#{entry['id']}@{page['anchor']}"

                elif (isbookpage(page, BookPage_hexcasting_pattern)
                and (url := _build_pattern_urls(registry, entry, page, base_url))):
                    registry.page_title_to_url[page["name"]] = url

                elif (isbookpage(page, BookPage_hexcasting_manual_pattern)
                and (url := _build_pattern_urls(registry, entry, page, base_url))):
                    registry.page_title_to_url[header_regex.sub("", page["header"])] = url

def build_registry() -> Registry:
    registry = Registry()
    hex_book: Book = hex_parse_book("HexMod/Common/src/main/resources", "hexcasting", "thehexbook")
    hexal_book: Book = hexal_parse_book("Hexal/Common/src/main/resources", "Hexal/doc/HexCastingResources", "hexal", "hexalbook")

    # translations
    for key, translation in dict(hex_book["i18n"], **hexal_book["i18n"]).items():
        if match := translation_regex.match(key):
            name = match[1]
            registry.name_to_translation[name] = translation.replace(": %s", "") # because the new built in decoding interferes with this
    
    # patterns
    for pattern_id, (pattern, direction, is_great) in dict(hex_book["pattern_reg"], **hexal_book["pattern_reg"]).items():
        name = pattern_id.split(":", 1)[1]
        if is_great:
            for segments in get_rotated_pattern_segments(Direction[direction], pattern):
                registry.great_spells[segments] = name
        else:
            registry.pattern_to_name[pattern] = name
        translation = registry.name_to_translation.get(name, name) # because Hexal sometimes doesn't have translations
        registry.translation_to_pattern[translation] = (Direction[direction], pattern, bool(is_great), name)
    
    # books
    _build_urls(registry, hex_book, HEX_BASE_URL)
    _build_urls(registry, hexal_book, HEXAL_BASE_URL)

    return registry
