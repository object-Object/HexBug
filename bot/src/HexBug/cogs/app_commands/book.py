from discord import Embed, Interaction, app_commands
from discord.ext.commands import GroupCog

from HexBug.core.cog import HexBugCog
from HexBug.utils.discord.transformers import ModInfoOption
from HexBug.utils.discord.visibility import (
    Visibility,
    VisibilityOption,
    respond_with_visibility,
)


class BookCog(HexBugCog, GroupCog, group_name="book"):
    @app_commands.command()
    async def home(
        self,
        interaction: Interaction,
        mod: ModInfoOption,
        visibility: VisibilityOption = Visibility.PRIVATE,
    ):
        embed = (
            Embed(
                title=mod.book_title,
                url=mod.book_url,
                description=mod.book_description,
            )
            .set_thumbnail(
                url=mod.icon_url,
            )
            .set_author(
                name=f"{mod.name} ({mod.pretty_version})",
            )
            .add_field(
                name="Categories",
                value=mod.category_count,
            )
            .add_field(
                name="Entries",
                value=mod.entry_count,
            )
            .add_field(
                name="Linkable Pages",
                value=mod.linkable_page_count,
            )
        )
        await respond_with_visibility(interaction, visibility, embed=embed)
