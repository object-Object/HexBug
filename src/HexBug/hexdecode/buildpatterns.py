import asyncio
import itertools
import logging
import re
from pathlib import Path
from typing import Any, Iterable, cast

from aiohttp import ClientSession
from hexdoc.minecraft import LocalizedStr
from hexdoc.patchouli import Category, FormatTree
from hexdoc.patchouli.page import SpotlightPage, TextPage
from hexdoc_hexcasting.book.page import (
    LookupPatternPage,
    PageWithOpPattern,
    PageWithPattern,
)

from HexBug.hexdecode.pregen_numbers import load_pregen_numbers
from HexBug.utils.hexdoc import format_text

from ..utils.api import APILocalPatternSource, APIPattern
from ..utils.book_types import (
    BookCategory,
    BookPage_hexcasting_manual_pattern,
    BookPage_hexcasting_pattern,
    BookPage_patchouli_spotlight,
    BookPage_patchouli_text,
)
from ..utils.extra_patterns import build_extra_patterns
from ..utils.mods import APIMod, APIWithBookModInfo, HexdocMod, Mod, RegistryMod
from ..utils.type_guards import is_typeddict_subtype
from .hex_math import Direction
from .registry import DuplicatePatternException, NormalPatternInfo, Registry

translation_regex = re.compile(r"hexcasting.spell.[a-z]+:(.+)")
header_regex = re.compile(r"\s*\(.+\)")


def _build_pattern_urls(
    registry: Registry,
    entry_id: str,
    page: BookPage_hexcasting_pattern
    | BookPage_hexcasting_manual_pattern
    | BookPage_patchouli_text,
    text: Any | None,
):
    match text:
        case str(description):
            pass
        case FormatTree():
            description = format_text(text)
        case _:
            description = None

    inp = f"__{inp}__" if (inp := page.get("input")) else ""
    oup = f"__{oup}__" if (oup := page.get("output")) else ""
    args = f"**{f'{inp} → {oup}'.strip()}**" if inp or oup else None

    url = f"#{entry_id}@{page['anchor']}" if "anchor" in page else None
    names: set[str] = set()
    if "op_id" in page:
        names.add(page["op_id"].split(":", 1)[1])

    # use .get with default to handle patchouli:text, which doesn't have op
    for pattern, _, _ in page.get(
        "op", []
    ):  # pretty sure this only catches the vector reflections right now
        if info := registry.from_pattern.get(pattern):
            names.add(info.name)

    for name in names:
        if info := registry.from_name.get(name):
            info.__late_init__(
                book_url=url,
                args=args,
                description=description,
            )

    if url is None:
        return None
    return (url, list(names))


# hacky...
def _build_hexdoc_pattern_urls(
    registry: Registry,
    entry_id: str,
    page: PageWithPattern,
    text: Any | None,
):
    raw_page = {}
    if page.input:
        raw_page["input"] = page.input
    if page.output:
        raw_page["output"] = page.output
    if page.anchor:
        raw_page["anchor"] = page.anchor
    if isinstance(page, PageWithOpPattern):
        raw_page["op_id"] = str(page.op_id)

    return _build_pattern_urls(
        registry,
        entry_id,
        cast(BookPage_hexcasting_pattern, raw_page),  # lie
        text,
    )


def _build_urls(registry: Registry, categories: list[BookCategory], mod: Mod):
    urls = registry.page_title_to_url[mod]

    for category in categories:
        urls[category["name"]] = (f"#{category['id']}", [])

        for entry in category["entries"]:
            urls[entry["name"]] = (f"#{entry['id']}", [])

            for page, next_page in itertools.zip_longest(
                entry["pages"],
                entry["pages"][1:],
                fillvalue=None,
            ):
                assert page is not None
                text = (
                    page.get("text")
                    or (
                        next_page
                        and is_typeddict_subtype(next_page, BookPage_patchouli_text)
                        and next_page.get("text")
                    )
                    or None
                )

                if (
                    is_typeddict_subtype(page, BookPage_patchouli_text)
                    and "title" in page
                    and "anchor" in page
                ):
                    urls[page["title"]] = (
                        f"#{entry['id']}@{page['anchor']}",
                        [],
                    )
                    _build_pattern_urls(registry, entry["id"], page, text)

                elif (
                    is_typeddict_subtype(page, BookPage_patchouli_spotlight)
                    and "anchor" in page
                ):
                    urls[page["item_name"]] = (
                        f"#{entry['id']}@{page['anchor']}",
                        [],
                    )

                elif is_typeddict_subtype(page, BookPage_hexcasting_pattern) and (
                    value := _build_pattern_urls(registry, entry["id"], page, text)
                ):
                    urls[page["name"]] = value

                elif is_typeddict_subtype(
                    page, BookPage_hexcasting_manual_pattern
                ) and (value := _build_pattern_urls(registry, entry["id"], page, text)):
                    urls[header_regex.sub("", page["header"])] = value


def _build_hexdoc_urls(registry: Registry, categories: Iterable[Category], mod: Mod):
    urls = registry.page_title_to_url[mod]

    for category in categories:
        urls[str(category.name)] = (f"#{category.id.path}", [])

        for entry in category.entries.values():
            urls[str(entry.name)] = (f"#{entry.id.path}", [])

            for page, next_page in itertools.zip_longest(
                entry.pages,
                entry.pages[1:],
                fillvalue=None,
            ):
                assert page is not None
                text = (
                    getattr(page, "text", None)
                    or (isinstance(next_page, TextPage) and next_page.text)
                    or None
                )

                match page:
                    case TextPage(title=LocalizedStr() as title, anchor=str(anchor)):
                        urls[str(title)] = (f"#{entry.id.path}@{anchor}", [])

                    case SpotlightPage(anchor=str(anchor)):
                        urls[str(page.item.name)] = (f"#{entry.id.path}@{anchor}", [])

                    case LookupPatternPage() if value := _build_hexdoc_pattern_urls(
                        registry,
                        entry.id.path,
                        page,
                        text,
                    ):
                        pattern = registry.from_name[page.patterns[0].id.path]
                        if pattern.translation:
                            urls[pattern.translation] = value

                    case PageWithPattern() if value := _build_hexdoc_pattern_urls(
                        registry,
                        entry.id.path,
                        page,
                        text,
                    ):
                        urls[header_regex.sub("", str(page.header))] = value


def _parse_i18n(name_to_translation: dict[str, str], i18n: dict[str, str]):
    for key, translation in i18n.items():
        if match := translation_regex.match(key):
            name = match[1]
            # because hexal has OLD VERSIONS of all the hex lang files
            if name in name_to_translation:
                continue
            # because the new built in decoding interferes with this
            # and because hex has the wrong names
            name_to_translation[name] = translation.replace(": %s", "").replace(
                "Dstl.", "Distillation"
            )


def _insert_classname(
    classname_to_path: dict[str, tuple[Mod, str]], classname: str, mod: Mod, path: str
):
    if (duplicate := classname_to_path.get(classname)) and duplicate[
        1
    ] != path:  # this *should* never happen
        raise Exception(f"Duplicate classname: {classname} ({path} and {duplicate[1]})")
    classname_to_path[classname] = (mod, path)


def merge_dicts(*dicts: dict[str, str]) -> dict[str, str]:
    output: dict[str, str] = {}
    for d in dicts:
        for key, value in d.items():
            if key not in output:
                output[key] = value
    return output


async def build_registry(session: ClientSession) -> Registry | None:
    logging.info("Building registry")

    pregen_numbers = load_pregen_numbers()

    registry = Registry(pregen_numbers)
    name_to_translation: dict[str, str] = {}
    classname_to_path: dict[str, tuple[Mod, str]] = {}
    api_mod_data: dict[APIMod, tuple[list[APIPattern], list[BookCategory]]] = {}

    # prerequisites for other processing: translations, classnames

    for mod in RegistryMod:
        mod_info = mod.value
        logging.info(f"Loading {mod_info.name} {mod_info.version}")

        # translations
        _parse_i18n(name_to_translation, mod_info.book["i18n"])

        # classnames
        for directory in mod_info.operator_directories:
            for file_path in Path(directory).rglob("Op*.kt"):
                file_path = Path(
                    *file_path.parts[2:]
                )  # eg. vendor/Hexal/Common/... -> Common/...
                _insert_classname(
                    classname_to_path, file_path.stem, mod, file_path.as_posix()
                )

        for info in build_extra_patterns(name_to_translation):
            if info.classname and info.class_mod and info.path:
                _insert_classname(
                    classname_to_path, info.classname, info.class_mod, info.path
                )

        for classname, path in mod_info.extra_classname_paths.items():
            _insert_classname(classname_to_path, classname, mod, path)

    for mod in APIMod:
        mod_info = mod.value
        logging.info(f"Loading {mod_info.name} {mod_info.version}")

        # fetch api data (this is the slow part)
        docs = await mod_info.api.get_docs(session)
        lang, patterns, categories = await asyncio.gather(
            mod_info.api.get_lang(session, docs),
            mod_info.api.get_patterns(session, docs),
            mod_info.api.get_book(session, docs),
        )
        api_mod_data[mod] = (patterns, categories)

        # translations
        _parse_i18n(name_to_translation, lang)

        # classnames
        for pattern in patterns:
            source = pattern["source"]
            if is_typeddict_subtype(source, APILocalPatternSource):
                _insert_classname(
                    classname_to_path,
                    pattern["className"].split(".")[-1],
                    mod,
                    source["path"],
                )

        # late init
        if isinstance(mod_info, APIWithBookModInfo):
            mod_info.__late_init__(
                docs["repositoryRoot"],
                mod_info.api.get_book_url(docs),
                docs["commitHash"],
            )
        else:
            mod_info.__late_init__(docs["repositoryRoot"], docs["commitHash"])

    for mod in HexdocMod:
        mod_info = mod.value
        logging.info(f"Loading {mod_info.name} {mod_info.version}")

        # translations
        assert mod_info.i18n.lookup is not None, f"Mod {mod.name} i18n.lookup is None"
        _parse_i18n(
            name_to_translation,
            {key: str(value) for key, value in mod_info.i18n.lookup.items()},
        )

        # TODO: load classnames

    # patterns and books

    duplicate_exceptions: list[DuplicatePatternException] = []

    for info in build_extra_patterns(name_to_translation):
        try:
            registry.add_pattern(info)
        except DuplicatePatternException as e:
            duplicate_exceptions.append(e)

    for mod in RegistryMod:
        mod_info = mod.value

        # in case a new pattern file was added to the mod (eg. Hexal adding Phase Block)
        # we don't just use this instead of mod_info.pattern_files because if this triggers, we also need to
        #   update mod_info.operator_directories
        docgen_pattern_files = set()
        for loader, stub in mod_info.pattern_stubs:
            filename = (
                Path(mod_info.book["resource_dir"]).parent / "java" / stub
            ).as_posix()
            if loader:
                filename = filename.replace("Common", loader)
            docgen_pattern_files.add(filename)

            # yes this is inefficient because it's a list
            # no i don't care, there's like at most three entries in each and it only runs once
            if filename not in mod_info.pattern_files:
                logging.warning(
                    f"Pattern file in {mod_info.name} docgen but not ModInfo: {filename}"
                )

        # patterns - can't use the Book data here because we also need the class name :pensivewobble:
        for filename in mod_info.pattern_files:
            if filename not in docgen_pattern_files:
                logging.warning(
                    f"Pattern file in {mod_info.name} ModInfo but not docgen: {filename}"
                )

            with open(filename, "r", encoding="utf-8") as file:
                for match in mod_info.registry_regex.finditer(file.read()):
                    if named_groups := match.groupdict():
                        # use named groups instead of assuming the order
                        pattern, direction, name, classname, is_great = (
                            named_groups["pattern"],
                            named_groups["direction"],
                            named_groups["name"],
                            named_groups["classname"],
                            named_groups["is_great"],
                        )
                    else:
                        (pattern, direction, name, classname, is_great) = match.groups()
                    class_mod, path = classname_to_path[classname]
                    try:
                        registry.add_pattern(
                            NormalPatternInfo(
                                name=name,
                                translation=name_to_translation.get(name),
                                mod=mod,
                                path=path,
                                classname=classname,
                                class_mod=class_mod,
                                is_great=bool(is_great),
                                direction=Direction[direction],
                                pattern=pattern,
                            )
                        )
                    except DuplicatePatternException as e:
                        duplicate_exceptions.append(e)

        # docs
        _build_urls(registry, mod_info.book["categories"], mod)

    for mod in APIMod:
        mod_info = mod.value
        patterns, categories = api_mod_data[mod]

        # patterns
        for pattern in patterns:
            source = pattern["source"]
            name = pattern["id"].split(":")[-1]
            classname = pattern["className"].split(".")[-1]

            if is_typeddict_subtype(source, APILocalPatternSource):
                class_mod = mod
                path = pattern["source"]["path"]
            else:
                class_mod, path = classname_to_path[classname]

            try:
                registry.add_pattern(
                    NormalPatternInfo(
                        name=name,
                        translation=name_to_translation.get(name),
                        mod=mod,
                        path=path,
                        classname=classname,
                        class_mod=class_mod,
                        is_great=pattern["isPerWorld"],
                        direction=Direction[pattern["defaultStartDir"]],
                        pattern=pattern["angleSignature"],
                    )
                )
            except DuplicatePatternException as e:
                duplicate_exceptions.append(e)

        if isinstance(mod_info, APIWithBookModInfo):
            _build_urls(registry, categories, mod)

    for mod in HexdocMod:
        mod_info = mod.value

        for pattern in mod_info.patterns:
            try:
                registry.add_pattern(
                    NormalPatternInfo(
                        name=pattern.name,
                        translation=name_to_translation.get(pattern.name),
                        mod=mod,
                        is_great=pattern.is_per_world,
                        direction=Direction[pattern.startdir.name],
                        pattern=pattern.signature,
                        class_mod=None,
                        classname=None,
                        path=None,
                    )
                )
            except DuplicatePatternException as e:
                duplicate_exceptions.append(e)

        _build_hexdoc_urls(registry, mod_info.book.categories.values(), mod)

    for pattern in registry.patterns:
        if pattern.book_url is None:
            logging.warning(f"No URL for pattern: {pattern}")
        if pattern.translation is None:
            logging.warning(f"No translation for pattern: {pattern}")

    if duplicate_exceptions:
        for e in duplicate_exceptions:
            message = [f"Duplicate pattern: {e.info or '(unknown)'}"]
            for duplicate in e.duplicates:
                value_display = (
                    duplicate.value
                    if isinstance(duplicate.value, (str, int, float, bool))
                    else type(duplicate.value)
                )
                message.append(
                    f'{"":34}{duplicate.info}.{duplicate.attribute} = "{value_display}"'
                )
            logging.error("\n".join(message))
        return None

    return registry
