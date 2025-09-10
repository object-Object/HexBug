import sqlalchemy as sa
from discord import Embed, Interaction, User, app_commands
from discord.app_commands import Transform
from discord.ext.commands import GroupCog

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
    PerWorldPatternTransformer,
)
from HexBug.utils.discord.translation import translate, translate_command_text
from HexBug.utils.discord.visibility import (
    Visibility,
    VisibilityOption,
    respond_with_visibility,
)
from HexBug.utils.per_world_patterns import add_per_world_pattern


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

        await add_per_world_pattern(
            interaction,
            pattern,
            info.id,
            self.bot.registry.display_pattern(info),
        )

    @app_commands.command()
    async def list(
        self,
        interaction: Interaction,
        contributor: User | None = None,
        visibility: VisibilityOption = Visibility.PRIVATE,
    ):
        assert interaction.guild

        async with self.bot.db_session() as session:
            stmt = sa.select(PerWorldPattern).where(
                PerWorldPattern.guild_id == interaction.guild.id
            )
            if contributor:
                stmt = stmt.where(PerWorldPattern.user_id == contributor.id)
            entries = await session.scalars(stmt)

        patterns = sorted(
            (
                (
                    info.name
                    if (info := self.bot.registry.patterns.get(entry.id))
                    else str(entry.id),
                    entry.pattern,
                )
                for entry in entries
            ),
            key=lambda v: v[0],
        )

        embed = Embed(
            title=await translate_command_text(interaction, "title"),
            description="\n".join(
                f"- {name}: `{pattern.display()}`" for name, pattern in patterns
            )
            if patterns
            else await translate_command_text(interaction, "no-patterns-found"),
        ).set_author(
            name=interaction.guild.name,
            icon_url=interaction.guild.icon.url if interaction.guild.icon else None,
        )

        if contributor:
            embed.set_footer(
                text=await translate(
                    interaction,
                    "per-world-pattern-contributor",
                    name=contributor.name,
                ),
                icon_url=contributor.display_avatar.url,
            )

        await respond_with_visibility(interaction, visibility, embed=embed)

    @app_commands.command()
    async def name(
        self,
        interaction: Interaction,
        entry: PerWorldPatternOption,
        visibility: VisibilityOption = Visibility.PRIVATE,
    ):
        view = await PerWorldPatternView.new(interaction, entry)
        await view.send(interaction, visibility)

    @app_commands.command()
    async def remove(
        self,
        interaction: Interaction,
        entry: Transform[
            PerWorldPattern,
            PerWorldPatternTransformer(autocomplete_filter_user=True),
        ],
    ):
        contributor = await self.bot.fetch_user(entry.user_id)
        if contributor != interaction.user:
            raise InvalidInputError(
                f"This pattern can only be removed by the user who added it ({contributor.name})."
                + " Use `/per-world-pattern-manage remove` to remove patterns added by other users.",
                fields=[],
            )

        async with self.bot.db_session() as session, session.begin():
            await session.delete(entry)

        view = await PerWorldPatternView.new(interaction, entry, contributor)
        await view.send(
            interaction,
            Visibility.PRIVATE,
            content=await translate_command_text(interaction, "removed"),
        )
