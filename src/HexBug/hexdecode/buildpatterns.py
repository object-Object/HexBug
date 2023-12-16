import asyncio
import json
import logging
import re
from pathlib import Path

from aiohttp import ClientSession

from ..utils.api import APILocalPatternSource, APIPattern
from ..utils.book_types import (
    BookCategory,
    BookEntry,
    BookPage_hexcasting_manual_pattern,
    BookPage_hexcasting_pattern,
    BookPage_patchouli_spotlight,
    BookPage_patchouli_text,
)
from ..utils.extra_patterns import build_extra_patterns
from ..utils.mods import APIMod, APIWithBookModInfo, Mod, RegistryMod
from ..utils.type_guards import is_typeddict_subtype
from .hex_math import Direction
from .registry import DuplicatePatternException, NormalPatternInfo, Registry

translation_regex = re.compile(r"hexcasting.spell.[a-z]+:(.+)")
header_regex = re.compile(r"\s*\(.+\)")

MAX_PREGEN_NUMBER = 2000
PREGEN_NUMBERS_FILE = (
    f"{Path(__file__).parent.as_posix()}/numbers_{MAX_PREGEN_NUMBER}.json"
)


def _build_pattern_urls(
    registry: Registry,
    entry: BookEntry,
    page: BookPage_hexcasting_pattern
    | BookPage_hexcasting_manual_pattern
    | BookPage_patchouli_text,
):
    inp = f"__{inp}__" if (inp := page.get("input")) else ""
    oup = f"__{oup}__" if (oup := page.get("output")) else ""
    args = f"**{f'{inp} → {oup}'.strip()}**" if inp or oup else None

    url = f"#{entry['id']}@{page['anchor']}" if "anchor" in page else None
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
            info.__late_init__(url, args)

    if url is None:
        return None
    return (url, list(names))


def _build_urls(registry: Registry, categories: list[BookCategory], mod: Mod):
    for category in categories:
        registry.page_title_to_url[mod][category["name"]] = (f"#{category['id']}", [])

        for entry in category["entries"]:
            registry.page_title_to_url[mod][entry["name"]] = (f"#{entry['id']}", [])

            for page in entry["pages"]:
                if (
                    is_typeddict_subtype(page, BookPage_patchouli_text)
                    and "title" in page
                    and "anchor" in page
                ):
                    registry.page_title_to_url[mod][page["title"]] = (
                        f"#{entry['id']}@{page['anchor']}",
                        [],
                    )
                    _build_pattern_urls(registry, entry, page)

                elif (
                    is_typeddict_subtype(page, BookPage_patchouli_spotlight)
                    and "anchor" in page
                ):
                    registry.page_title_to_url[mod][page["item_name"]] = (
                        f"#{entry['id']}@{page['anchor']}",
                        [],
                    )

                elif is_typeddict_subtype(page, BookPage_hexcasting_pattern) and (
                    value := _build_pattern_urls(registry, entry, page)
                ):
                    registry.page_title_to_url[mod][page["name"]] = value

                elif is_typeddict_subtype(
                    page, BookPage_hexcasting_manual_pattern
                ) and (value := _build_pattern_urls(registry, entry, page)):
                    registry.page_title_to_url[mod][
                        header_regex.sub("", page["header"])
                    ] = value


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

    with open(PREGEN_NUMBERS_FILE, "r", encoding="utf-8") as f:
        pregen_numbers = {
            int(n): (Direction[d], p) for n, (d, p) in json.load(f).items()
        }

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

    for pattern in registry.patterns:
        if pattern.book_url is None:
            logging.warning(f"No URL for pattern: {pattern}")
        if pattern.translation is None:
            logging.warning(f"No translation for pattern: {pattern}")

    if duplicate_exceptions:
        for e in duplicate_exceptions:
            message = [f"Duplicate pattern: {e.info}"]
            for attribute, duplicate in e.duplicates:
                value = getattr(e.info, attribute)
                value_display = (
                    value if isinstance(value, (str, int, float, bool)) else type(value)
                )
                message.append(f'{"":34}{duplicate}.{attribute} = "{value_display}"')
            logging.error("\n".join(message))
        return None

    return registry
