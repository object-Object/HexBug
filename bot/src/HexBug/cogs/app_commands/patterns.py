import asyncio
from dataclasses import dataclass
from datetime import timedelta
from enum import Enum
from fractions import Fraction

from discord import Embed, Interaction, Message, app_commands
from discord.app_commands import Transform
from discord.ext.commands import GroupCog
from hex_renderer_py import PatternVariant

from HexBug.core.cog import HexBugCog
from HexBug.core.exceptions import InvalidInputError
from HexBug.data.hex_math import HexPattern
from HexBug.data.patterns import PatternInfo
from HexBug.data.special_handlers import SpecialHandlerPattern
from HexBug.data.utils.lehmer import swizzle
from HexBug.data.utils.shorthand import PUNCTUATION
from HexBug.data.utils.strings import format_number
from HexBug.rendering.draw import to_pattern_variant
from HexBug.ui.views.patterns import (
    DrawPatternsView,
    EmbedPatternView,
    NamedPatternView,
)
from HexBug.utils.discord.embeds import EmbedField
from HexBug.utils.discord.translation import (
    LocaleEnumTransformer,
    translate_command_text,
)
from HexBug.utils.discord.visibility import Visibility, VisibilityOption
from HexBug.utils.numbers import DecomposedNumber

MAX_NUMBER = 1e12
MAX_LENGTH = 48


class StackOrder(Enum):
    TOP_TO_BOTTOM = "top_to_bottom"
    BOTTOM_TO_TOP = "bottom_to_top"


StackOrderOption = Transform[
    StackOrder, LocaleEnumTransformer(StackOrder, name="value")
]


@dataclass(eq=False)
class PatternsCog(HexBugCog, GroupCog, group_name="patterns"):
    def __post_init__(self):
        self.draw_messages = dict[int, DrawMessage]()

    @app_commands.command()
    async def draw(
        self,
        interaction: Interaction,
        show_signatures: bool = False,
        visibility: VisibilityOption = Visibility.PRIVATE,
    ):
        empty_text = await translate_command_text(interaction, "empty")

        def on_send_as_public(i: Interaction):
            self.draw_messages[interaction.user.id].interaction = i
            self.draw_messages[interaction.user.id].message = None

        view = DrawPatternsView(
            interaction=interaction,
            patterns=[],
            hide_stroke_order=False,
            embed=Embed(description=empty_text),
            add_footer=show_signatures,
            on_send_as_public=on_send_as_public,
            on_stop_drawing=lambda: self.draw_messages.pop(interaction.user.id, None),
        )
        view.clear_items()
        view.add_items(interaction, visibility, None)

        _, message = await asyncio.gather(
            interaction.response.launch_activity(),
            interaction.followup.send(
                embeds=await view.get_embeds(interaction),
                files=view.get_attachments(),
                view=view,
                ephemeral=visibility.ephemeral,
                wait=True,
            ),
        )

        view.clear_items()
        view.add_items(interaction, visibility, message)
        await view.refresh(interaction, message)

        self.draw_messages[interaction.user.id] = DrawMessage(
            view, interaction, message, empty_text
        )

    @app_commands.command()
    async def hex(
        self,
        interaction: Interaction,
        hex: str,
        show_signatures: bool = False,
        visibility: VisibilityOption = Visibility.PRIVATE,
    ):
        patterns = list[PatternVariant]()

        # allow eg. { mind } compass
        for punctuation in PUNCTUATION:
            hex = hex.replace(punctuation, f",{punctuation},")

        for shorthand in hex.split(","):
            shorthand = shorthand.strip()
            if not shorthand:
                continue

            match self.bot.registry.try_match_shorthand(shorthand):
                case PatternInfo(pattern=pattern, is_per_world=is_per_world):
                    patterns.append(to_pattern_variant(pattern, is_per_world))
                case SpecialHandlerPattern(pattern=pattern) | (HexPattern() as pattern):
                    patterns.append(to_pattern_variant(pattern))
                case None:
                    raise InvalidInputError("Unrecognized pattern.", value=shorthand)

        await EmbedPatternView(
            interaction=interaction,
            patterns=patterns,
            hide_stroke_order=False,
            embed=Embed(),
            add_footer=show_signatures,
        ).send(interaction, visibility)

    @app_commands.command()
    async def number(
        self,
        interaction: Interaction,
        number: str,
        visibility: VisibilityOption = Visibility.PRIVATE,
    ):
        if len(number) > MAX_LENGTH:
            raise InvalidInputError("Number is too large.", value=number)

        try:
            target = Fraction(number)
        except Exception as e:
            raise InvalidInputError("Invalid number.", value=number) from e

        if abs(target.numerator) > MAX_NUMBER or abs(target.denominator) > MAX_NUMBER:
            raise InvalidInputError("Number is too large.", value=number)

        await self._generate_and_display(
            interaction=interaction,
            target=target,
            visibility=visibility,
        )

    @app_commands.command()
    async def swindler(
        self,
        interaction: Interaction,
        order: StackOrderOption,
        before: str,
        after: str,
        visibility: VisibilityOption = Visibility.PRIVATE,
    ):
        if "," in before:
            stack_before = before.split(",")
            stack_after = after.split(",")
        elif " " in before:
            stack_before = before.split(" ")
            stack_after = after.split(" ")
        else:
            stack_before = list(before)
            stack_after = list(after)

        if order is StackOrder.TOP_TO_BOTTOM:
            stack_before.reverse()
            stack_after.reverse()

        if len(stack_before) != len(stack_after):
            raise InvalidInputError(
                "Stack size before and after does not match.",
                fields=[
                    EmbedField(name="Before", value="\n".join(reversed(stack_before))),
                    EmbedField(name="After", value="\n".join(reversed(stack_after))),
                ],
            )

        stack_before = [v.lower().strip() for v in stack_before]
        stack_after = [v.lower().strip() for v in stack_after]

        if sorted(stack_before) != sorted(stack_after):
            raise InvalidInputError(
                "Stack elements before and after do not match.",
                fields=[
                    EmbedField(name="Before", value="\n".join(reversed(stack_before))),
                    EmbedField(name="After", value="\n".join(reversed(stack_after))),
                ],
            )

        code = swizzle(before=stack_before, after=stack_after)

        if abs(code) > MAX_NUMBER:
            raise InvalidInputError(
                "Generated Lehmer code is too large to render.", value=code
            )

        await self._generate_and_display(
            interaction=interaction,
            target=code,
            visibility=visibility,
        )

    async def _generate_and_display(
        self,
        *,
        interaction: Interaction,
        target: int | Fraction,
        visibility: Visibility,
    ):
        result = await asyncio.get_running_loop().run_in_executor(
            None,
            DecomposedNumber.generate_or_decompose,
            target,
            self.bot.registry.pregenerated_numbers,
            timedelta(seconds=1),
        )

        if result.is_equation:
            await EmbedPatternView(
                interaction=interaction,
                patterns=result.patterns,
                hide_stroke_order=False,
                embed=Embed(
                    title=format_number(result.value),
                    description=f"```\n{result.equation}\n```",
                ),
            ).send(interaction, visibility)
        else:
            await NamedPatternView(
                interaction=interaction,
                pattern=result.patterns[0],
                hide_stroke_order=False,
                info=self.bot.registry.try_match_pattern(result.patterns[0]),
            ).send(interaction, visibility)


@dataclass
class DrawMessage:
    view: DrawPatternsView
    interaction: Interaction
    message: Message | None
    empty_text: str
