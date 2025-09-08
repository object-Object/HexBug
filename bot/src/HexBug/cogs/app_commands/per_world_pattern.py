from discord import Interaction, app_commands
from discord.ext.commands import GroupCog
from psycopg.errors import UniqueViolation
from sqlalchemy.exc import IntegrityError

from HexBug.core.cog import HexBugCog
from HexBug.core.exceptions import InvalidInputError
from HexBug.data.hex_math import HexPattern
from HexBug.data.patterns import PatternInfo
from HexBug.db.models import PerWorldPattern
from HexBug.ui.views.patterns import PerWorldPatternView
from HexBug.utils.discord.transformers import (
    HexDirOption,
    PatternSignatureOption,
    PerWorldPatternOption,
)
from HexBug.utils.discord.visibility import Visibility, VisibilityOption


@app_commands.guild_install()
@app_commands.guild_only()
class PerWorldPatternCog(HexBugCog, GroupCog, group_name="per-world-pattern"):
    @app_commands.command()
    async def add(
        self,
        interaction: Interaction,
        direction: HexDirOption,
        signature: PatternSignatureOption,
    ):
        assert interaction.guild_id

        # look up the pattern to make sure it's actually per-world
        pattern = HexPattern(direction, signature)
        match self.bot.registry.try_match_pattern(pattern):
            case PatternInfo(is_per_world=True, display_only=False) as info:
                pass
            case None:
                raise InvalidInputError("Unknown pattern.", value=pattern.display())
            case match:
                raise InvalidInputError(
                    "Pattern is not per-world.",
                    value=pattern.display(),
                ).add_field(
                    name="Pattern",
                    value=self.bot.registry.display_pattern(match).name,
                )

        # insert the pattern
        try:
            async with self.bot.db_session() as session, session.begin():
                session.add(
                    PerWorldPattern(
                        id=info.id,
                        guild_id=interaction.guild_id,
                        user_id=interaction.user.id,
                        direction=direction,
                        signature=signature,
                    )
                )
        except IntegrityError as e:
            if isinstance(e.orig, UniqueViolation):
                raise InvalidInputError(
                    "Pattern has already been added to this server's database.",
                    value=pattern.display(),
                ).add_field(
                    name="Pattern",
                    value=self.bot.registry.display_pattern(info).name,
                )
            raise

        await PerWorldPatternView(
            interaction=interaction,
            pattern=pattern,
            pattern_id=info.id,
            info=info,
            contributor=interaction.user,
            add_visibility_buttons=False,
        ).send(
            interaction,
            Visibility.PRIVATE,
            content="Pattern added.",
        )

    @app_commands.command()
    async def name(
        self,
        interaction: Interaction,
        entry: PerWorldPatternOption,
        visibility: VisibilityOption = Visibility.PRIVATE,
    ):
        await PerWorldPatternView(
            interaction=interaction,
            pattern=entry.pattern,
            pattern_id=entry.id,
            info=self.bot.registry.patterns.get(entry.id),
            contributor=await self.bot.fetch_user(entry.user_id),
        ).send(interaction, visibility)
