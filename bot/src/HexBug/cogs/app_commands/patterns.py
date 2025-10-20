import asyncio
from datetime import timedelta
from fractions import Fraction

from discord import Embed, Interaction, app_commands
from discord.ext.commands import GroupCog

from HexBug.core.cog import HexBugCog
from HexBug.core.exceptions import InvalidInputError
from HexBug.data.hex_math import HexPattern
from HexBug.data.patterns import PatternInfo
from HexBug.data.special_handlers import SpecialHandlerPattern
from HexBug.data.utils.shorthand import PUNCTUATION
from HexBug.data.utils.strings import format_number
from HexBug.ui.views.patterns import EmbedPatternView, NamedPatternView
from HexBug.utils.discord.visibility import Visibility, VisibilityOption
from HexBug.utils.numbers import DecomposedNumber

MAX_NUMBER = 1e12
MAX_LENGTH = 48


class PatternsCog(HexBugCog, GroupCog, group_name="patterns"):
    @app_commands.command()
    async def hex(
        self,
        interaction: Interaction,
        hex: str,
        visibility: VisibilityOption = Visibility.PRIVATE,
    ):
        patterns = list[HexPattern]()

        # allow eg. { mind } compass
        for punctuation in PUNCTUATION:
            hex = hex.replace(punctuation, f",{punctuation},")

        for shorthand in hex.split(","):
            shorthand = shorthand.strip()
            if not shorthand:
                continue

            match self.bot.registry.try_match_shorthand(shorthand):
                case (
                    PatternInfo(pattern=pattern)
                    | SpecialHandlerPattern(pattern=pattern)
                    | (HexPattern() as pattern)
                ):
                    patterns.append(pattern)
                case None:
                    raise InvalidInputError("Unrecognized pattern.", value=shorthand)

        await EmbedPatternView(
            interaction=interaction,
            patterns=patterns,
            hide_stroke_order=False,
            embed=Embed(),
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

        if target.numerator > MAX_NUMBER or target.denominator > MAX_NUMBER:
            raise InvalidInputError("Number is too large.", value=number)

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
