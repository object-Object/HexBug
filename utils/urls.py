def wrap_url(url: str, show_spoilers: bool, escape: bool) -> str:
    if escape:
        url = f"<{url}>"
    if show_spoilers:
        # spoiler the link to make it clear that you'll see spoilers if you click it
        url = f"||{url}||"
    return url
