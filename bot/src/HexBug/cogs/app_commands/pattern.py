from __future__ import annotations

from collections import defaultdict
from enum import Enum
from typing import Any

from discord import Color, Embed, Interaction, app_commands
from discord.app_commands import Transform
from discord.ext.commands import GroupCog
from hexdoc.core import ResourceLocation

from HexBug.core.cog import HexBugCog
from HexBug.core.exceptions import InvalidInputError
from HexBug.data.hex_math import HexDir, HexPattern
from HexBug.data.registry import PatternMatchResult
from HexBug.data.special_handlers import SpecialHandlerMatch
from HexBug.data.static_data import SPECIAL_HANDLERS
from HexBug.ui.views.patterns import (
    EmbedPatternView,
    NamedPatternView,
    PatternBuilderView,
)
from HexBug.utils.discord.transformers import (
    HexDirOption,
    PatternInfoOption,
    PatternSignatureOption,
    SpecialHandlerInfoOption,
)
from HexBug.utils.discord.translation import (
    LocaleEnumTransformer,
    translate_command_text,
)
from HexBug.utils.discord.visibility import Visibility, VisibilityOption


class PatternCheckType(Enum):
    NORMAL = "normal"
    PER_WORLD = "per_world"
    SPECIAL_PREFIX = "special_prefix"


PatternCheckTypeOption = Transform[
    PatternCheckType, LocaleEnumTransformer(PatternCheckType, name="value")
]


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
            parsed_value, pattern = handler.generate_pattern(self.bot.registry, value)
        except ValueError as e:
            raise InvalidInputError(
                f"Failed to parse value for {info.base_name}.", value=value
            ) from e
        except NotImplementedError as e:
            raise InvalidInputError(
                f"Generating {info.base_name} is not yet supported.", fields=[]
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
        pattern_type: PatternCheckTypeOption,
        direction: HexDirOption = HexDir.EAST,
        visibility: VisibilityOption = Visibility.PRIVATE,
    ):
        registry = self.bot.registry
        pattern = HexPattern(direction, signature)

        conflicts = dict[ResourceLocation, tuple[str, PatternMatchResult]]()
        if conflict := registry.try_match_pattern(pattern):
            conflicts[conflict.id] = ("signature", conflict)

        match pattern_type:
            case PatternCheckType.NORMAL:
                pass

            case PatternCheckType.PER_WORLD:
                segments = pattern.get_aligned_segments()
                for conflict in registry.lookups.segments.get(segments, []):
                    conflicts[conflict.id] = ("shape", conflict)

            case PatternCheckType.SPECIAL_PREFIX:
                for info in registry.patterns.values():
                    if info.signature.startswith(signature):
                        conflicts[info.id] = ("prefix", info)

        title = await translate_command_text(
            interaction, "title", conflicts=len(conflicts)
        )

        if conflicts:
            embed = Embed(
                title=title,
                color=Color.red(),
            )

            fields = defaultdict[str, list[str]](list)
            for conflict_type, conflict in conflicts.values():
                fields[conflict_type].append(
                    f"- {registry.display_pattern(conflict).name} (`{conflict.id}`)"
                )

            for conflict_type, lines in fields.items():
                embed.add_field(
                    name=await translate_command_text(
                        interaction, f"conflict-{conflict_type}"
                    ),
                    value="\n".join(lines),
                    inline=False,
                )
        else:
            embed = Embed(
                title=title,
                color=Color.green(),
            )

        await EmbedPatternView(
            interaction=interaction,
            patterns=[pattern],
            hide_stroke_order=pattern_type is PatternCheckType.PER_WORLD,
            embed=embed,
        ).send(interaction, visibility)

    @app_commands.command()
    async def build(self, interaction: Interaction, hide_stroke_order: bool = False):
        await PatternBuilderView(
            interaction=interaction,
            hide_stroke_order=hide_stroke_order,
        ).send(interaction, Visibility.PRIVATE)
