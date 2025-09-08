from __future__ import annotations

from typing import Any

from discord import Color, Embed, Interaction, app_commands
from discord.ext.commands import GroupCog
from hexdoc.core import ResourceLocation

from HexBug.core.cog import HexBugCog
from HexBug.core.exceptions import InvalidInputError
from HexBug.data.hex_math import HexDir, HexPattern
from HexBug.data.registry import PatternMatchResult
from HexBug.data.special_handlers import SpecialHandlerMatch
from HexBug.data.static_data import SPECIAL_HANDLERS
from HexBug.ui.views.patterns import EmbedPatternView, NamedPatternView
from HexBug.utils.discord.transformers import (
    HexDirOption,
    PatternInfoOption,
    PatternSignatureOption,
    SpecialHandlerInfoOption,
)
from HexBug.utils.discord.translation import translate_command_text
from HexBug.utils.discord.visibility import Visibility, VisibilityOption


class PatternCog(HexBugCog, GroupCog, group_name="pattern"):
    @app_commands.command()
    async def name(
        self,
        interaction: Interaction,
        info: PatternInfoOption,
        visibility: VisibilityOption = Visibility.PRIVATE,
    ):
        display_info = self.bot.registry.display_pattern(info)
        await NamedPatternView(
            interaction=interaction,
            pattern=display_info.pattern,
            hide_stroke_order=display_info.is_per_world,
            info=info,
            display_info=display_info,
        ).send(interaction, visibility)

    @app_commands.command()
    async def special(
        self,
        interaction: Interaction,
        info: SpecialHandlerInfoOption,
        value: str,
        visibility: VisibilityOption = Visibility.PRIVATE,
    ):
        handler = SPECIAL_HANDLERS[info.id]
        try:
            parsed_value, pattern = handler.parse_value(self.bot.registry, value)
        except ValueError as e:
            raise InvalidInputError(
                f"Failed to parse value for {info.base_name}.", value=value
            ) from e

        await NamedPatternView(
            interaction=interaction,
            pattern=pattern,
            info=SpecialHandlerMatch[Any].from_parts(
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
        direction: HexDirOption,
        signature: PatternSignatureOption,
        hide_stroke_order: bool = False,
        visibility: VisibilityOption = Visibility.PRIVATE,
    ):
        pattern = HexPattern(direction, signature)

        info = self.bot.registry.try_match_pattern(pattern)

        await NamedPatternView(
            interaction=interaction,
            pattern=pattern,
            info=info,
            hide_stroke_order=hide_stroke_order,
        ).send(interaction, visibility)

    @app_commands.command()
    async def check(
        self,
        interaction: Interaction,
        signature: PatternSignatureOption,
        is_per_world: bool,
        visibility: VisibilityOption = Visibility.PRIVATE,
    ):
        pattern = HexPattern(HexDir.EAST, signature)

        conflicts = dict[ResourceLocation, PatternMatchResult]()

        if conflict := self.bot.registry.try_match_pattern(pattern):
            conflicts[conflict.id] = conflict

        if is_per_world:
            segments = pattern.get_aligned_segments()
            for conflict in self.bot.registry.lookups.segments.get(segments, []):
                conflicts[conflict.id] = conflict

        title = await translate_command_text(
            interaction, "title", conflicts=len(conflicts)
        )

        if conflicts:
            embed = Embed(
                title=title,
                description="\n".join(
                    f"- {self.bot.registry.display_pattern(conflict).name} (`{conflict.id}`)"
                    for conflict in conflicts.values()
                ),
                color=Color.red(),
            )
        else:
            embed = Embed(
                title=title,
                color=Color.green(),
            )

        await EmbedPatternView(
            interaction=interaction,
            pattern=pattern,
            hide_stroke_order=is_per_world,
            embed=embed,
        ).send(interaction, visibility)
