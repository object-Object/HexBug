from typing import Any


def truncate_str(text: str, limit: int | None, message: str = "..."):
    if limit is None:
        return text

    limit -= len(message)
    if len(text) <= limit:
        return text

    return text[:limit] + message


def join_truthy(joiner: str, *values: Any) -> str:
    return joiner.join(str(v) for v in values if v)


def format_number(n: float) -> str:
    return f"{n:,}".rstrip("0").rstrip(".").replace(",", " ")
