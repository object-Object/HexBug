from typing import Any

import sqlalchemy as sa
from discord import ButtonStyle, Color, Interaction, User, app_commands
from discord.ext.commands import GroupCog
from discord.ui import ActionRow, Button, Container, LayoutView, TextDisplay
from sqlalchemy import func

from HexBug.core.bot import HexBugBot
from HexBug.core.cog import HexBugCog
from HexBug.core.exceptions import InvalidInputError
from HexBug.data.hex_math import HexPattern
from HexBug.data.patterns import PatternInfo
from HexBug.data.special_handlers import SpecialHandlerMatch
from HexBug.db.models import PerWorldPattern
from HexBug.ui.views.patterns import PerWorldPatternView
from HexBug.utils.discord.transformers import (
    HexDirOption,
    PatternSignatureOption,
    PerWorldPatternOption,
    ResourceLocationOption,
)
from HexBug.utils.discord.translation import translate_command_text
from HexBug.utils.discord.visibility import Visibility
from HexBug.utils.per_world_patterns import add_per_world_pattern


@app_commands.guild_install()
@app_commands.guild_only()
@app_commands.default_permissions(manage_messages=True)
class PerWorldPatternManageCog(
    HexBugCog, GroupCog, group_name="per-world-pattern-manage"
):
    @app_commands.command()
    async def add(
        self,
        interaction: Interaction,
        pattern_id: ResourceLocationOption,
        direction: HexDirOption,
        signature: PatternSignatureOption,
    ):
        pattern = HexPattern(direction, signature)
        match self.bot.registry.try_match_pattern(pattern):
            case PatternInfo(is_per_world=True, display_only=False) as info:
                if info.id != pattern_id:
                    raise InvalidInputError(
                        "A pattern with this shape exists, but does not match the provided ID.",
                        value=f"`{pattern_id}`",
                    ).add_field(
                        name="Pattern",
                        value=f"{self.bot.registry.display_pattern(info).name} (`{info.id}`)",
                    )

            case PatternInfo() as info:
                raise InvalidInputError(
                    "A pattern with this shape exists, but is not per-world.",
                    value=pattern.display(),
                ).add_field(
                    name="Pattern",
                    value=self.bot.registry.display_pattern(info).name,
                )

            # we allow special handler matches in case an addon adds a per-world pattern that conflicts with a special handler
            # like craft phial, for instance
            case SpecialHandlerMatch() | None:
                if info := self.bot.registry.patterns.get(pattern_id):
                    raise InvalidInputError(
                        "A pattern with this ID exists, but does not match the provided shape.",
                        value=pattern.display(),
                    ).add_field(
                        name="Pattern",
                        value=self.bot.registry.display_pattern(info).name,
                    )

        await add_per_world_pattern(
            interaction,
            HexPattern(direction, signature),
            pattern_id,
            info,
        )

    @app_commands.command()
    async def remove(self, interaction: Interaction, entry: PerWorldPatternOption):
        async with self.bot.db_session() as session, session.begin():
            await session.delete(entry)

        view = await PerWorldPatternView.new(interaction, entry)
        await view.send(
            interaction,
            Visibility.PRIVATE,
            content=await translate_command_text(interaction, "removed"),
        )

    @app_commands.command(name="remove-all")
    async def remove_all(
        self,
        interaction: Interaction,
        contributor: User | None = None,
    ):
        assert interaction.guild_id

        async with self.bot.db_session() as session:
            stmt = sa.select(func.count(PerWorldPattern.id)).where(
                PerWorldPattern.guild_id == interaction.guild_id
            )
            if contributor:
                stmt = stmt.where(PerWorldPattern.user_id == contributor.id)
            count = await session.scalar(stmt)

        if not count:
            if contributor:
                raise InvalidInputError(
                    "No patterns have been added to this server by this user.",
                    value=contributor.name,
                )
            else:
                raise InvalidInputError(
                    "No patterns found in this server to delete.", fields=[]
                )

        await interaction.response.send_message(
            view=await RemoveAllView().async_init(interaction, count, contributor),
            ephemeral=True,
        )


class RemoveAllView(LayoutView):
    async def async_init(
        self,
        interaction: Interaction,
        count: int,
        contributor: User | None,
    ):
        self.interaction = interaction
        self.count = count
        self.contributor = contributor
        self.bot = HexBugBot.of(interaction)

        self.container.add_item(
            TextDisplay(
                await translate_command_text(
                    interaction, "confirm-user", count=count, user=contributor.name
                )
                if contributor
                else await translate_command_text(
                    interaction, "confirm-all", count=count
                )
            ),
        )

        self.remove_item(self.row)
        self.container.add_item(self.row)

        self.cancel_button.label = await translate_command_text(interaction, "cancel")
        self.remove_button.label = await translate_command_text(
            interaction, "remove", count=count
        )

        return self

    container = Container[Any]()

    row = ActionRow[Any]()

    @row.button(style=ButtonStyle.gray)
    async def cancel_button(
        self,
        interaction: Interaction,
        button: Button[Any],
    ):
        self.container.clear_items()
        self.container.add_item(
            TextDisplay(await translate_command_text(self.interaction, "cancelled"))
        )
        self.container.accent_color = Color.red()
        await interaction.response.edit_message(view=self)

    @row.button(style=ButtonStyle.red)
    async def remove_button(
        self,
        interaction: Interaction,
        button: Button[Any],
    ):
        async with self.bot.db_session() as session, session.begin():
            stmt = sa.delete(PerWorldPattern).where(
                PerWorldPattern.guild_id == interaction.guild_id
            )
            if self.contributor:
                stmt = stmt.where(PerWorldPattern.user_id == self.contributor.id)
            await session.execute(stmt)

        self.container.clear_items()
        self.container.add_item(
            TextDisplay(
                await translate_command_text(
                    self.interaction, "removed", count=self.count
                )
            )
        )
        self.container.accent_color = Color.green()
        await interaction.response.edit_message(view=self)
