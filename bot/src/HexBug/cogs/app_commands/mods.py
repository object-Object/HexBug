from discord import Embed, Interaction, app_commands

from HexBug.core.cog import HexBugCog
from HexBug.utils.discord.transformers import ModAuthorOption, ModloaderOption
from HexBug.utils.discord.translation import translate_text
from HexBug.utils.discord.visibility import MessageVisibility, respond_with_visibility


class ModsCog(HexBugCog):
    @app_commands.command()
    async def mods(
        self,
        interaction: Interaction,
        author: ModAuthorOption | None = None,
        modloader: ModloaderOption | None = None,
        visibility: MessageVisibility = "private",
    ):
        mods = [
            mod
            for mod in self.bot.registry.mods.values()
            if (author is None or mod.github_author == author)
            and (modloader is None or modloader in mod.modloaders)
        ]

        # TODO: this will eventually need to be paginated
        embed = Embed(
            title=await translate_text(
                interaction,
                "title",
                modloader=modloader.value if modloader else "None",
            ),
            description="\n".join(
                f"* **[{mod.name}]({mod.book_url})** ({mod.pretty_version})"
                for mod in mods
            )
            if mods
            else await translate_text(interaction, "no-mods-found"),
        ).set_footer(
            text=await translate_text(
                interaction,
                "footer-filtered" if author or modloader else "footer-normal",
                mods=len(mods),
                total=len(self.bot.registry.mods),
            ),
        )

        if author:
            embed.set_author(
                name=author,
                url=f"https://github.com/{author}",
                icon_url=f"https://github.com/{author}.png",
            )

        await respond_with_visibility(interaction, visibility, embed=embed)
