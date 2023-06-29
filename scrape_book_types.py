import asyncio
from collections import defaultdict
from typing import Any, Callable, Mapping

from aiohttp import ClientSession

from HexBug.utils.mods import APIMod, RegistryMod

if __name__ != "__main__":
    raise Exception("please don't try to actually use this code in production lmao")

BookKeys = defaultdict[str, set[str]]
BookNotRequired = set[str]


def add_keys(item: Mapping[str, Any], keys: BookKeys, _: BookNotRequired) -> None:
    for key, value in item.items():
        keys[key].add(value.__class__.__name__)


def add_not_required(item: Mapping[str, Any], keys: BookKeys, not_required: BookNotRequired) -> None:
    not_required |= set(keys.keys()).difference(set(item.keys()))


def set_value_where(keys: BookKeys, key: str, value: set[str], new_value: set[str]) -> None:
    if key in keys:
        if keys[key] == value:
            keys[key] = new_value
        else:
            raise ValueError(key, value, keys[key])
    else:
        raise KeyError(key)


def print_class(name: str, keys: BookKeys, not_required: BookNotRequired, total=True, parent="TypedDict"):
    print(f"\nclass {name}({parent}{', total=False' if not total else ''}):")
    for item in sorted(keys.items(), key=lambda i: (i[0] in not_required, i[0])):
        key, values = item
        value = " | ".join(sorted(values))
        if total:
            if key in not_required:
                print(f"    {key}: NotRequired[{value}]")
            else:
                print(f"    {key}: {value}")
        else:
            if key in not_required:
                print(f"    {key}: {value}")
            else:
                print(f"    {key}: Required[{value}]")
    if len(keys) == 0:
        print("    pass")


# don't use this in production
async def _get_categories() -> list:
    categories = []

    for mod in RegistryMod:
        categories.extend(mod.value.book["categories"])

    async with ClientSession() as session:
        for mod in APIMod:
            api = mod.value.api
            docs = await api.get_docs(session)
            categories.extend(await api.get_book(session, docs))

    return categories


# also don't use this in production
categories = asyncio.run(_get_categories())

book_keys: BookKeys = defaultdict(set)
book_not_required: BookNotRequired = set()
category_keys: BookKeys = defaultdict(set)
category_not_required: BookNotRequired = set()
entry_keys: BookKeys = defaultdict(set)
entry_not_required: BookNotRequired = set()
page_types: defaultdict[str, tuple[BookKeys, BookNotRequired]] = defaultdict(lambda: (defaultdict(set), set()))


def update_book(update: Callable[[Mapping[str, Any], BookKeys, BookNotRequired], None]) -> None:
    for mod in RegistryMod:
        update(mod.value.book, book_keys, book_not_required)
    for category in categories:
        update(category, category_keys, category_not_required)
        for entry in category["entries"]:
            update(entry, entry_keys, entry_not_required)
            for page in entry["pages"]:
                page_keys, page_not_required = page_types[page["type"]]
                update(page, page_keys, page_not_required)
                # if update == add_keys and page["type"] == "hexcasting:manual_pattern" and "op_id" not in page:
                #     print(page, end="\n\n")


update_book(add_keys)
update_book(add_not_required)

set_value_where(entry_keys, "pages", {"list"}, {f"list[BookPage]"})
set_value_where(category_keys, "entries", {"list"}, {f"list[BookEntry]"})
set_value_where(book_keys, "categories", {"list"}, {f"list[BookCategory]"})

print(
    """from typing import Generic, Literal, LiteralString, NotRequired, TypedDict, TypeVar

from HexMod.doc.collate_data import FormatTree

T = TypeVar("T", bound=LiteralString)
class BookPage(TypedDict, Generic[T]):
    type: T"""
)

for t, (page_keys, page_not_required) in page_types.items():
    page_keys.pop("type")
    print_class(
        f"BookPage_{t.replace(':', '_')}",
        page_keys,
        page_not_required,
        parent=f'BookPage[Literal["{t}"]]',
    )

print_class("BookEntry", entry_keys, entry_not_required)
print_class("BookCategory", category_keys, category_not_required)
print_class("Book", book_keys, book_not_required)
