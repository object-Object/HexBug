from discord import Embed, Interaction, app_commands

from HexBug.core.cog import HexBugCog
from HexBug.utils.discord.embeds import FOOTER_SEPARATOR, EmbedField, add_fields
from HexBug.utils.discord.transformers import ModInfoOption
from HexBug.utils.discord.visibility import MessageVisibility, respond_with_visibility


class ModCog(HexBugCog):
    @app_commands.command()
    async def mod(
        self,
        interaction: Interaction,
        mod: ModInfoOption,
        visibility: MessageVisibility = "private",
    ):
        embed = (
            Embed(
                title=mod.name,
                url=mod.book_url,
                description=mod.description,
            )
            .set_thumbnail(
                url=mod.icon_url,
            )
            .set_footer(
                text=FOOTER_SEPARATOR.join(
                    [
                        mod.id,
                        mod.version,
                    ]
                ),
            )
        )

        github_commit = mod.github_commit[:8]
        github_commit_url = mod.github_url / "tree" / mod.github_commit

        add_fields(
            embed,
            EmbedField(
                name="Supported Loaders",
                value="\n".join(
                    f"{self.bot.get_modloader_emoji(modloader)} {modloader.value}"
                    for modloader in mod.modloaders
                ),
            ),
            EmbedField(
                name="CurseForge",
                value=mod.curseforge_url,
            ),
            EmbedField(
                name="Modrinth",
                value=mod.modrinth_url,
            ),
            EmbedField(
                name="GitHub",
                value=f"{mod.github_url} ([{github_commit}]({github_commit_url}))",
            ),
            skip_falsy=True,
            default_inline=False,
        )

        await respond_with_visibility(interaction, visibility, embed=embed)
