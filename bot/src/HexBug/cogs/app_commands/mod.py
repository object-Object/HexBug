from discord import Embed, Interaction, app_commands

from HexBug.core.cog import HexBugCog
from HexBug.utils.discord.embeds import FOOTER_SEPARATOR, EmbedField, add_fields
from HexBug.utils.discord.transformers import ModInfoOption
from HexBug.utils.discord.translation import translate_command_text
from HexBug.utils.discord.visibility import (
    Visibility,
    VisibilityOption,
    respond_with_visibility,
)


class ModCog(HexBugCog):
    @app_commands.command()
    async def mod(
        self,
        interaction: Interaction,
        mod: ModInfoOption,
        visibility: VisibilityOption = Visibility.PRIVATE,
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
                name=await translate_command_text(interaction, "modloaders"),
                value="\n".join(
                    f"{self.bot.get_modloader_emoji(modloader)} {modloader.value}"
                    for modloader in mod.modloaders
                ),
            ),
            EmbedField(
                name=await translate_command_text(interaction, "curseforge"),
                value=mod.curseforge_url,
            ),
            EmbedField(
                name=await translate_command_text(interaction, "modrinth"),
                value=mod.modrinth_url,
            ),
            EmbedField(
                name=await translate_command_text(interaction, "github"),
                value=f"{mod.github_url} ([{mod.github_commit[:8]}]({mod.github_permalink}))",
            ),
            skip_falsy=True,
            default_inline=False,
        )
        add_fields(
            embed,
            EmbedField(
                name=await translate_command_text(interaction, "patterns"),
                value=mod.pattern_count,
            ),
            EmbedField(
                name=await translate_command_text(interaction, "overloads"),
                value=await translate_command_text(
                    interaction,
                    "overloads-value",
                    first_party=mod.first_party_operator_count
                    - mod.documented_pattern_count,
                    third_party=mod.third_party_operator_count,
                ),
            ),
            EmbedField(
                name=await translate_command_text(interaction, "special"),
                value=mod.special_handler_count,
            ),
            EmbedField(
                name=await translate_command_text(interaction, "categories"),
                value=mod.category_count,
            ),
            EmbedField(
                name=await translate_command_text(interaction, "entries"),
                value=mod.entry_count,
            ),
            EmbedField(
                name=await translate_command_text(interaction, "pages"),
                value=mod.linkable_page_count,
            ),
            EmbedField(
                name=await translate_command_text(interaction, "recipes"),
                value=mod.recipe_count,
            ),
            skip_falsy=False,
            default_inline=True,
        )

        await respond_with_visibility(interaction, visibility, embed=embed)
