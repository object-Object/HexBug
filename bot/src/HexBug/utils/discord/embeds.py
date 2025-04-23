from dataclasses import dataclass
from typing import Any

from discord import Embed

FOOTER_SEPARATOR = "  •  "


@dataclass(kw_only=True)
class EmbedField:
    name: Any
    value: Any
    inline: bool | None = None


def add_fields(
    embed: Embed,
    *fields: EmbedField,
    skip_falsy: bool = False,
    default_inline: bool = True,
):
    """Adds several fields to an embed.

    If `skip_falsy` is True, skips any fields with a falsy value.
    """
    for field in fields:
        if skip_falsy and not field.value:
            continue
        embed.add_field(
            name=field.name,
            value=field.value,
            inline=field.inline if field.inline is not None else default_inline,
        )
    return embed
