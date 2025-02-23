def truncate_str(text: str, limit: int | None, message: str = "..."):
    if limit is None:
        return text

    limit -= len(message)
    if len(text) <= limit:
        return text

    return text[:limit] + message
