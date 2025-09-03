import textwrap

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
                text=FOOTER_SEPARATOR.join([
                    mod.id,
                    mod.pretty_version,
                ]),
            )
        )

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
                value=f"{mod.github_url} ([{mod.github_commit[:8]}]({mod.github_permalink}))",
            ),
            skip_falsy=True,
            default_inline=False,
        )
        add_fields(
            embed,
            EmbedField(
                name="Patterns",
                value=mod.pattern_count,
            ),
            EmbedField(
                name="Overloads",
                value=textwrap.dedent(
                    f"""\
                    {mod.first_party_operator_count - mod.pattern_count} first-party
                    {mod.third_party_operator_count} third-party
                    """
                ),
            ),
            EmbedField(
                name="Special Handlers",
                value=mod.special_handler_count,
            ),
            skip_falsy=False,
            default_inline=True,
        )

        await respond_with_visibility(interaction, visibility, embed=embed)
