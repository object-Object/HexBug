from typing import Any

from discord import ui


def update_indexed_select_menu(select: ui.Select[Any]) -> list[int]:
    indices = set(int(value) for value in select.values)
    result = list[int]()
    for i, option in enumerate(select.options):
        option.default = i in indices
        if option.default:
            result.append(i)
    return result
