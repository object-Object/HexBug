import itertools
from typing import Iterable

from discord import Embed, Interaction, app_commands

from HexBug.core.cog import HexBugCog
from HexBug.data.mods import ModInfo
from HexBug.ui.views.paginated import ButtonPaginatedView
from HexBug.utils.discord.transformers import ModAuthorOption, ModloaderOption
from HexBug.utils.discord.translation import translate_command_text
from HexBug.utils.discord.visibility import (
    Visibility,
    VisibilityOption,
    respond_with_visibility,
)


class ModsCog(HexBugCog):
    @app_commands.command()
    async def mods(
        self,
        interaction: Interaction,
        author: ModAuthorOption | None = None,
        modloader: ModloaderOption | None = None,
        visibility: VisibilityOption = Visibility.PRIVATE,
    ):
        mods = [
            mod
            for mod in self.bot.registry.mods.values()
            if (author is None or mod.source.author == author)
            and (modloader is None or modloader in mod.modloaders)
        ]

        embed = Embed(
            title=await translate_command_text(
                interaction,
                "title",
                modloader=modloader.value if modloader else "None",
            ),
        ).set_footer(
            text=await translate_command_text(
                interaction,
                "footer-filtered" if author or modloader else "footer-normal",
                mods=len(mods),
                total=len(self.bot.registry.mods),
            ),
        )

        if author:
            embed.set_author(
                name=author.name,
                url=author.url,
                icon_url=author.icon_url,
            )

        if mods:
            await ButtonPaginatedView(
                user=interaction.user,
                command=interaction.command,
                embeds=[
                    copy_with_description(embed, chunk)
                    for chunk in itertools.batched(mods, 25)
                ],
            ).send(interaction, visibility)
        else:
            embed.description = await translate_command_text(
                interaction, "no-mods-found"
            )
            await respond_with_visibility(interaction, visibility, embed=embed)


def copy_with_description(embed: Embed, mods: Iterable[ModInfo]):
    embed = embed.copy()
    embed.description = "\n".join(
        f"* **[{mod.name}]({mod.book_url})** ({mod.pretty_version})" for mod in mods
    )
    return embed
