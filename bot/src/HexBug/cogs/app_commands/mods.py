from discord import Embed, Interaction, app_commands

from HexBug.core.cog import HexBugCog
from HexBug.utils.discord.transformers import ModAuthorOption
from HexBug.utils.discord.visibility import MessageVisibility, respond_with_visibility


class ModsCog(HexBugCog):
    @app_commands.command()
    async def mods(
        self,
        interaction: Interaction,
        author: ModAuthorOption | None = None,
        visibility: MessageVisibility = "private",
    ):
        if author:
            mods = [
                mod
                for mod in self.bot.registry.mods.values()
                if mod.github_author == author
            ]
        else:
            mods = self.bot.registry.mods.values()

        footer = f"Count: {len(mods)}"
        if author:
            footer += f"/{len(self.bot.registry.mods)}"

        # TODO: this will eventually need to be paginated
        embed = Embed(
            title="Loaded Mods",
            description="\n".join(
                f"* **[{mod.name}]({mod.book_url})** ({mod.pretty_version})"
                for mod in mods
            ),
        ).set_footer(
            text=footer,
        )

        if author:
            embed.set_author(
                name=author,
                url=f"https://github.com/{author}",
                icon_url=f"https://github.com/{author}.png",
            )

        await respond_with_visibility(interaction, visibility, embed=embed)
