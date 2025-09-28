import random

from discord import Color, Embed, Interaction, app_commands
from discord.ext.commands import GroupCog
from yarl import URL

from HexBug.core.cog import HexBugCog
from HexBug.utils.discord.embeds import set_embed_mod_author
from HexBug.utils.discord.transformers import (
    CategoryInfoOption,
    EntryInfoOption,
    ModInfoOption,
    PageInfoOption,
    RecipeInfoOption,
)
from HexBug.utils.discord.translation import translate_command_text
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
                name=await translate_command_text(interaction, "categories"),
                value=mod.category_count,
            )
            .add_field(
                name=await translate_command_text(interaction, "entries"),
                value=mod.entry_count,
            )
            .add_field(
                name=await translate_command_text(interaction, "pages"),
                value=mod.linkable_page_count,
            )
            .add_field(
                name=await translate_command_text(interaction, "recipes"),
                value=mod.recipe_count,
            )
        )
        await respond_with_visibility(interaction, visibility, embed=embed)

    @app_commands.command()
    async def category(
        self,
        interaction: Interaction,
        category: CategoryInfoOption,
        visibility: VisibilityOption = Visibility.PRIVATE,
    ):
        embed = Embed(
            title=await translate_command_text(
                interaction, "title", name=category.name
            ),
            url=category.url,
            description=category.description,
        ).set_footer(
            text=category.id,
        )

        set_embed_mod_author(embed, self.bot.registry.mods[category.mod_id])
        _set_icon(embed, category.icon_urls)

        await respond_with_visibility(interaction, visibility, embed=embed)

    @app_commands.command()
    async def entry(
        self,
        interaction: Interaction,
        entry: EntryInfoOption,
        visibility: VisibilityOption = Visibility.PRIVATE,
    ):
        category = self.bot.registry.categories[entry.category_id]

        embed = (
            Embed(
                title=await translate_command_text(
                    interaction, "title", name=entry.name
                ),
                url=entry.url,
                color=Color.from_str(f"0x{entry.color.value}") if entry.color else None,
            )
            .set_footer(
                text=f"{entry.id} ({entry.category_id})",
            )
            .add_field(
                name=await translate_command_text(interaction, "category"),
                value=f"[{category.name}]({category.url})",
            )
        )

        set_embed_mod_author(embed, self.bot.registry.mods[entry.mod_id])
        _set_icon(embed, entry.icon_urls)

        await respond_with_visibility(interaction, visibility, embed=embed)

    @app_commands.command()
    async def page(
        self,
        interaction: Interaction,
        page: PageInfoOption,
        visibility: VisibilityOption = Visibility.PRIVATE,
    ):
        entry = self.bot.registry.entries[page.entry_id]
        category = self.bot.registry.categories[entry.category_id]

        embed = (
            Embed(
                title=await translate_command_text(
                    interaction, "title", title=page.title
                ),
                url=page.url,
                description=page.text,
            )
            .set_footer(
                text=f"{page.key} ({category.id})",
            )
            .add_field(
                name=await translate_command_text(interaction, "category"),
                value=f"[{category.name}]({category.url})",
            )
            .add_field(
                name=await translate_command_text(interaction, "entry"),
                value=f"[{entry.name}]({entry.url})",
            )
        )

        set_embed_mod_author(embed, self.bot.registry.mods[page.mod_id])
        _set_icon(embed, page.icon_urls)

        await respond_with_visibility(interaction, visibility, embed=embed)

    @app_commands.command()
    async def recipe(
        self,
        interaction: Interaction,
        recipes: RecipeInfoOption,
        visibility: VisibilityOption = Visibility.PRIVATE,
    ):
        embeds = list[Embed]()

        for recipe in recipes:
            page = self.bot.registry.pages[recipe.page_key] if recipe.page_key else None
            entry = self.bot.registry.entries[recipe.entry_id]
            category = self.bot.registry.categories[entry.category_id]

            embed = (
                Embed(
                    title=await translate_command_text(
                        interaction, "title", title=recipe.name
                    ),
                    url=page.url if page else entry.url,
                    description=recipe.description,
                )
                .set_footer(
                    text=f"{recipe.id} ({recipe.type})",
                )
                .add_field(
                    name=await translate_command_text(interaction, "category"),
                    value=f"[{category.name}]({category.url})",
                )
                .add_field(
                    name=await translate_command_text(interaction, "entry"),
                    value=f"[{entry.name}]({entry.url})",
                )
            )
            if page:
                embed.add_field(
                    name=await translate_command_text(interaction, "page"),
                    value=f"[{page.title}]({page.url})",
                )

            set_embed_mod_author(embed, self.bot.registry.mods[recipe.mod_id])
            _set_icon(embed, recipe.icon_urls)

            embeds.append(embed)

        await respond_with_visibility(interaction, visibility, embeds=embeds)


def _set_icon(embed: Embed, icon_urls: list[URL]):
    if icon_urls:
        embed.set_thumbnail(
            url=random.choice(icon_urls),  # teehee
        )
    return embed
