from __future__ import annotations

from discord import Color, Embed, Interaction, app_commands
from discord.app_commands import Transform
from discord.app_commands.transformers import EnumNameTransformer
from discord.ext.commands import GroupCog
from hexdoc.core import ResourceLocation

from HexBug.core.cog import HexBugCog
from HexBug.core.exceptions import InvalidInputError
from HexBug.core.translator import translate_text
from HexBug.data.hex_math import VALID_SIGNATURE_PATTERN, HexDir, HexPattern
from HexBug.data.registry import PatternMatchResult
from HexBug.data.special_handlers import SpecialHandlerMatch
from HexBug.data.static_data import SPECIAL_HANDLERS
from HexBug.ui.views.patterns import PatternView
from HexBug.utils.discord.transformers import (
    PatternInfoOption,
    SpecialHandlerInfoOption,
)
from HexBug.utils.discord.visibility import (
    MessageVisibility,
    respond_with_visibility,
)

PATTERN_FILENAME = "pattern.png"


class PatternCog(HexBugCog, GroupCog, group_name="pattern"):
    @app_commands.command()
    @app_commands.rename(info="name")
    async def name(
        self,
        interaction: Interaction,
        info: PatternInfoOption,
        visibility: MessageVisibility = "private",
    ):
        await PatternView(
            interaction=interaction,
            pattern=info.pattern,
            info=info,
            hide_stroke_order=info.is_per_world,
        ).send(interaction, visibility)

    @app_commands.command()
    @app_commands.rename(info="name")
    async def special(
        self,
        interaction: Interaction,
        info: SpecialHandlerInfoOption,
        value: str,
        visibility: MessageVisibility = "private",
    ):
        handler = SPECIAL_HANDLERS[info.id]
        try:
            parsed_value, pattern = handler.parse_value(self.bot.registry, value)
        except ValueError as e:
            raise InvalidInputError(
                value, f"Failed to parse value for {info.base_name}."
            ) from e

        await PatternView(
            interaction=interaction,
            pattern=pattern,
            info=SpecialHandlerMatch(
                handler=handler,
                info=info,
                value=parsed_value,
            ),
            hide_stroke_order=False,
        ).send(interaction, visibility)

    @app_commands.command()
    async def raw(
        self,
        interaction: Interaction,
        direction: Transform[HexDir, EnumNameTransformer(HexDir)],
        signature: str,
        visibility: MessageVisibility = "private",
        hide_stroke_order: bool = False,
    ):
        signature = validate_signature(signature)
        pattern = HexPattern(direction, signature)

        info = self.bot.registry.try_match_pattern(pattern)

        await PatternView(
            interaction=interaction,
            pattern=pattern,
            info=info,
            hide_stroke_order=hide_stroke_order,
        ).send(interaction, visibility)

    @app_commands.command()
    async def check(
        self,
        interaction: Interaction,
        signature: str,
        is_per_world: bool,
        visibility: MessageVisibility = "private",
    ):
        signature = validate_signature(signature)
        pattern = HexPattern(HexDir.EAST, signature)

        conflicts = dict[ResourceLocation, PatternMatchResult]()

        if conflict := self.bot.registry.try_match_pattern(pattern):
            conflicts[conflict.id] = conflict

        if is_per_world:
            segments = pattern.get_aligned_segments()
            for conflict in self.bot.registry.lookups.segments.get(segments, []):
                conflicts[conflict.id] = conflict

        title = await translate_text(interaction, "title", conflicts=len(conflicts))

        if conflicts:
            embed = Embed(
                title=title,
                description="\n".join(
                    f"- {conflict.name} (`{conflict.id}`)"
                    for conflict in conflicts.values()
                ),
                color=Color.red(),
            )
        else:
            embed = Embed(
                description=title,
                color=Color.green(),
            )

        await respond_with_visibility(interaction, visibility, embed=embed)


def validate_signature(signature: str) -> str:
    signature = signature.lower()
    if signature in ["-", '"-"']:
        signature = ""
    elif not VALID_SIGNATURE_PATTERN.fullmatch(signature):
        raise InvalidInputError(
            value=signature,
            message="Invalid signature, must only contain the characters `aqweds`.",
        )
    return signature
