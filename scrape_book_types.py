from collections import defaultdict
from HexMod.doc.collate_data import parse_book
from Hexal.doc.collate_data import parse_book as hexal_parse_book
from hexast import Book
from typing import Any, Literal, Mapping

if __name__ != "__main__":
    raise Exception("please don't try to actually use this code in production lmao")

def update(item: Mapping[str, Any], keys: set[tuple[str, str]], not_required: set[tuple[str, str]]):
    current_keys = set((k, v.__class__.__name__) for k, v in item.items())
    not_required |= keys.difference(current_keys)
    keys |= current_keys

def unionize(keys: set[tuple[str, str]], not_required: set[tuple[str, str]]) -> set[tuple[str, str]]:
    new_keys: dict[str, str] = {}
    for item in keys:
        k, t = item
        if k in new_keys:
            new_keys[k] += f" | {t}"
        else:
            new_keys[k] = t
        if item in not_required:
            not_required.remove(item)
            not_required.add((k, new_keys[k]))
    return set(new_keys.items())

def print_class(name: str, keys: set[tuple[str, str]], not_required: set[tuple[str, str]], total=True, parent="TypedDict"):
    print(f"\nclass {name}({parent}{', total=False' if not total else ''}):")
    for item in sorted(unionize(keys, not_required), key=lambda i: (i in not_required, i[0])):
        key, value = item
        if total:
            if item in not_required:
                print(f"    {key}: NotRequired[{value}]")
            else:
                print(f"    {key}: {value}")
        else:
            if item in not_required:
                print(f"    {key}: {value}")
            else:
                print(f"    {key}: Required[{value}]")
    if len(keys) == 0:
        print("    pass")

hex_book: Book = parse_book("HexMod/Common/src/main/resources", "hexcasting", "thehexbook")
hexal_book: Book = hexal_parse_book("Hexal/Common/src/main/resources", "Hexal/doc/HexCastingResources", "hexal", "hexalbook")

category_keys: set[tuple[str, str]] = set()
category_not_required: set[tuple[str, str]] = set()
entry_keys: set[tuple[str, str]] = set()
entry_not_required: set[tuple[str, str]] = set()
page_types: defaultdict[str, tuple[
    set[tuple[str, str]],
    set[tuple[str, str]],
]] = defaultdict(lambda: (set(), set()))

for _ in range(2): # this needs to happen twice for, uh, algorithm reasons
    for category in hex_book["categories"] + hexal_book["categories"]:
        update(category, category_keys, category_not_required)
        for entry in category["entries"]:
            update(entry, entry_keys, entry_not_required)
            for page in entry["pages"]:
                page_keys, page_not_required = page_types[page["type"]]
                update(page, page_keys, page_not_required)
                if page["type"] == "hexcasting:manual_pattern" and "anchor" in page:
                    print(page)

print("""T = TypeVar("T", bound=LiteralString)
class BookPage(TypedDict, Generic[T]):
    type: T""")
for t, (page_keys, page_not_required) in page_types.items():
    print_class(
        f"BookPage_{t.replace(':', '_')}",
        page_keys.difference([("type", "str")]),
        page_not_required,
        parent=f'BookPage[Literal["{t}"]]',
    )
print_class("BookEntry", entry_keys, entry_not_required)
print_class("BookCategory", category_keys, category_not_required)
