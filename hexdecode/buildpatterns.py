import logging
import re
from pathlib import Path
from typing import TypeVar

from hexdecode.hex_math import Direction
from hexdecode.hexast import Registry, get_rotated_pattern_segments
from utils.book_types import (
    Book,
    BookEntry,
    BookPage_hexcasting_manual_pattern,
    BookPage_hexcasting_pattern,
    BookPage_patchouli_spotlight,
    BookPage_patchouli_text,
)
from utils.book_utils import isbookpage
from utils.mods import APIMod, Mod, RegistryMod

translation_regex = re.compile(r"hexcasting.spell.[a-z]+:(.+)")
header_regex = re.compile(r"\s*\(.+\)")


class DuplicatePatternException(Exception):
    def __init__(self, name1: str, name2: str, pattern: str, is_great: bool) -> None:
        super().__init__(f"Duplicate {'great spell' if is_great else 'pattern'} ({name1}, {name2}): {pattern}")


def _build_pattern_urls(
    registry: Registry,
    entry: BookEntry,
    page: BookPage_hexcasting_pattern | BookPage_hexcasting_manual_pattern,
    mod: Mod,
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


def _build_urls(registry: Registry, book: Book, mod: Mod):
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
    classname_to_path: dict[str, tuple[Mod, str]],
    direction: Direction,
    pattern: str,
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
    registry.translation_to_path[translation] = (*classname_to_path[classname], name, classname)


def merge_dicts(*dicts: dict[str, str]) -> dict[str, str]:
    output: dict[str, str] = {}
    for d in dicts:
        for key, value in d.items():
            if key not in output:
                output[key] = value
    return output


def build_registry() -> Registry:
    logging.log(logging.INFO, "building registry")

    registry = Registry()
    classname_to_path: dict[str, tuple[Mod, str]] = {}

    for mod in RegistryMod:
        registry.translation_to_path.update(
            {translation: (mod, *vals) for translation, vals in mod.value.extra_translation_paths.items()}
        )
        classname_to_path.update(
            {classname: (mod, path) for classname, path in mod.value.extra_classname_paths.items()}
        )

    # translations
    for key, translation in merge_dicts(*(mod.value.book["i18n"] for mod in RegistryMod)).items():
        if match := translation_regex.match(key):
            name = match[1]
            # because the new built in decoding interferes with this
            registry.name_to_translation[name] = translation.replace(": %s", "")

    for mod in RegistryMod:
        for directory in mod.value.operator_directories:
            for path in Path(directory).rglob("Op*.kt"):
                final_path = path.relative_to(path.parts[0])
                key = final_path.stem
                if duplicate := classname_to_path.get(key):  # this *should* never happen
                    raise Exception(f"Duplicate classname: {key} ({final_path} and {duplicate})")
                classname_to_path[key] = (mod, final_path.as_posix())

        # patterns - can't use the Book data here because we also need the class name :pensivewobble:
        for filename in mod.value.pattern_files:
            with open(filename, "r", encoding="utf-8") as file:
                for match in mod.value.registry_regex.finditer(file.read()):
                    (pattern, direction, name, classname, is_great) = match.groups()
                    _add_to_registry(
                        registry=registry,
                        classname_to_path=classname_to_path,
                        direction=Direction[direction],
                        pattern=pattern,
                        name=name,
                        classname=classname,
                        is_great=bool(is_great),
                    )

        for pattern_info in mod.value.special_patterns:
            _add_to_registry(registry, classname_to_path, **pattern_info.add_to_registry_kwargs)

        _build_urls(registry, mod.value.book, mod)

    return registry
