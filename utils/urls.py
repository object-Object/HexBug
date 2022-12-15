from utils.mods import Mod


def build_book_url(mod: Mod, url: str, show_spoilers: bool, escape: bool) -> str:
    book_url = f"{mod.value.book_url}{'?nospoiler' if show_spoilers else ''}{url}"
    if escape:
        book_url = f"<{book_url}>"
    if show_spoilers:
        # spoiler the link to make it clear that you'll see spoilers if you click it
        book_url = f"||{book_url}||"
    return book_url
