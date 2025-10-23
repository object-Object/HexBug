import random

from discord import Color, Embed, Interaction, app_commands
from discord.ext.commands import GroupCog
from hexdoc.core import ResourceLocation
from tantivy import Occur, Query
from yarl import URL

from HexBug.core.cog import HexBugCog
from HexBug.core.exceptions import InvalidInputError
from HexBug.data.registry import BookIndexField
from HexBug.utils.discord.embeds import set_embed_mod_author
from HexBug.utils.discord.transformers import (
    CategoryInfoOption,
    EntryInfoOption,
    ModInfoOption,
    PageInfoOption,
    RecipeInfoOption,
)
from HexBug.utils.discord.translation import translate, translate_command_text
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
                name=await translate(interaction, "book-category"),
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
                name=await translate(interaction, "book-category"),
                value=f"[{category.name}]({category.url})",
            )
            .add_field(
                name=await translate(interaction, "book-entry"),
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
                    name=await translate(interaction, "book-category"),
                    value=f"[{category.name}]({category.url})",
                )
                .add_field(
                    name=await translate(interaction, "book-entry"),
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

    @app_commands.command()
    async def search(
        self,
        interaction: Interaction,
        query: str,
        mod: ModInfoOption | None = None,
        visibility: VisibilityOption = Visibility.PRIVATE,
    ):
        registry = self.bot.registry
        index = self.bot.book_index
        searcher = index.searcher()

        try:
            parsed_query = index.parse_query(
                query=query,
                default_field_names=[BookIndexField.TITLE, BookIndexField.TEXT],
            )
        except Exception as e:
            raise InvalidInputError("Invalid query.", value=query).add_field(
                name="Tantivy Query Info",
                value="https://docs.rs/tantivy/latest/tantivy/query/struct.QueryParser.html",
            ) from e

        if mod:
            parsed_query = Query.boolean_query([
                (Occur.Must, parsed_query),
                (
                    Occur.Must,
                    Query.term_query(index.schema, BookIndexField.MOD_ID, mod.id),
                ),
            ])

        search_result = searcher.search(parsed_query, limit=25)
        if not search_result.hits:
            raise InvalidInputError("No results found.", value=query).add_field(
                name="Tantivy Query Info",
                value="https://docs.rs/tantivy/latest/tantivy/query/struct.QueryParser.html",
            )

        # FIXME: use a dropdown to select between results instead of showing all of them at once

        embeds = list[Embed]()
        for _, address in search_result.hits[:3]:
            doc = {
                name: values[0]
                for name, values in searcher.doc(address).to_dict().items()
                if values
            }

            mod = registry.mods[doc[BookIndexField.MOD_ID]]

            category_id = ResourceLocation.from_str(doc[BookIndexField.CATEGORY_ID])
            category = registry.categories[category_id]

            embed = Embed(
                title=doc.get(BookIndexField.TITLE),
                description=doc.get(BookIndexField.TEXT_MARKDOWN),
            )
            set_embed_mod_author(embed, mod)

            if (page_index := doc.get(BookIndexField.PAGE_INDEX)) is not None:
                # page
                entry_id = ResourceLocation.from_str(doc[BookIndexField.ENTRY_ID])
                entry = registry.entries[entry_id]

                if not embed.title:
                    embed.title = await translate(
                        interaction,
                        "book-placeholder-page-title",
                        entry=entry.name,
                        index=page_index + 1,
                    )

                (
                    embed.add_field(
                        name=await translate(interaction, "book-category"),
                        value=f"[{category.name}]({category.url})",
                    ).add_field(
                        name=await translate(interaction, "book-entry"),
                        value=f"[{entry.name}]({entry.url})",
                    )
                )

                if (anchor := doc.get(BookIndexField.PAGE_ANCHOR)) and (
                    page := registry.pages.get(f"{entry_id}#{anchor}")
                ):
                    embed.url = str(page.url)
                else:
                    anchor = page_index
                    embed.url = str(entry.url)

                embed.set_footer(text=f"{entry_id}#{anchor} ({category.id})")

            else:
                # category
                embed.url = str(category.url)
                embed.set_footer(text=category.id)

            embeds.append(embed)

        await respond_with_visibility(interaction, visibility, embeds=embeds)


def _set_icon(embed: Embed, icon_urls: list[URL]):
    if icon_urls:
        embed.set_thumbnail(
            url=random.choice(icon_urls),  # teehee
        )
    return embed
