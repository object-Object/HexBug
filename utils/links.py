from hexdecode.hexast import MOD_INFO, ModName


def build_book_url(mod: ModName, url: str, show_spoilers: bool, escape: bool) -> str:
    book_url = f"{MOD_INFO[mod].book_url}{'?nospoiler' if show_spoilers else ''}{url}"
    if escape:
        book_url = f"<{book_url}>"
    if show_spoilers:
        book_url = f"||{book_url}||"
    return book_url


def build_source_url(mod: ModName, path: str):
    return f"{MOD_INFO[mod].source_url}{'blob/main/' if path else ''}{path}"
