import asyncio
from collections import defaultdict
from dataclasses import asdict
from io import BytesIO
import logging
import os
from typing import Literal, assert_never
import discord
from discord import app_commands
from discord.ext import commands
import revealparser
from hexast import Registry, Direction, _parse_unknown_pattern, UnknownPattern, generate_bookkeeper, massage_raw_pattern_list, ModName, MOD_INFO
from buildpatterns import build_registry
from dotenv import load_dotenv
from generate_image import generate_image, Palette
from tags import Tag, Tags

DEFAULT_LINE_SCALE = 6
DEFAULT_ARROW_SCALE = 2
SCALE_RANGE = app_commands.Range[float, 0.1, 1000.]

class MessageCommandsCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.command()
    @commands.guild_only()
    @commands.is_owner()
    async def sync(self, ctx: commands.Context):
        """Sync slash commands to this guild"""
        assert ctx.guild
        async with ctx.channel.typing():
            self.bot.tree.copy_global_to(guild=ctx.guild)
            await self.bot.tree.sync(guild=ctx.guild)
        await ctx.reply("✅ Synced slash commands to this guild.")
    
    @commands.command()
    @commands.guild_only()
    @commands.is_owner()
    async def global_sync(self, ctx: commands.Context):
        """Sync slash commands to all guilds"""
        assert ctx.guild
        async with ctx.channel.typing():
            await self.bot.tree.sync()
        await ctx.reply("✅ Synced slash commands to all guilds (may take up to an hour to update everywhere).")

class EventsCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Logged in as {self.bot.user}")

class PatternCog(commands.GroupCog, name="pattern"):
    def __init__(self, bot: commands.Bot, registry: Registry) -> None:
        self.bot = bot
        self.registry = registry

        initial_choices: list[tuple[app_commands.Choice[str], list[str]]] = []
        for name, translation in registry.name_to_translation.items():
            if translation == "Numerical Reflection": continue
            if translation == "Bookkeeper's Gambit": translation += ": …"
            initial_choices.append((app_commands.Choice(name=translation, value=translation), [name]))
        
        self.autocomplete = build_autocomplete(initial_choices)

        super().__init__()
    
    @app_commands.command()
    @app_commands.describe(
        direction="The starting direction of the pattern",
        pattern='The angle signature of the pattern (eg. aqaawde) — type "-" to leave blank',
        show_to_everyone="Whether the result should be visible to everyone, or just you (to avoid spamming)",
        hide_stroke_order="Whether or not to hide the stroke order (like with great spells)",
        palette="The color palette to use for the lines (has no effect if hide_stroke_order is True)",
        line_scale="The scale of the lines and dots in the image",
        arrow_scale="The scale of the arrows in the image",
    )
    async def raw(
        self,
        interaction: discord.Interaction,
        direction: Direction,
        pattern: app_commands.Range[str, 1, 256],
        show_to_everyone: bool = False,
        hide_stroke_order: bool = False,
        palette: Palette = Palette.Classic,
        line_scale: SCALE_RANGE = DEFAULT_LINE_SCALE,
        arrow_scale: SCALE_RANGE = DEFAULT_ARROW_SCALE,
    ) -> None:
        """Display the stroke order of a pattern from its direction and angle signature"""
        if pattern in ["-", '"-"']:
            pattern = ""
        elif not all(c in "aqwed" for c in pattern):
            return await interaction.response.send_message(
                "❌ Invalid angle signature, must only contain the characters `aqwed`.",
                ephemeral=True,
            )
        
        pattern_iota, name = _parse_unknown_pattern(UnknownPattern(direction, pattern), self.registry)
        translation = pattern_iota.localize(self.registry)

        await send_pattern(
            self.registry,
            interaction,
            name,
            translation,
            generate_image(direction, pattern, hide_stroke_order, palette, line_scale, arrow_scale),
            not show_to_everyone,
        )

    @app_commands.command()
    @app_commands.describe(
        translation="The name of the pattern",
        show_to_everyone="Whether the result should be visible to everyone, or just you (to avoid spamming)",
        palette="The color palette to use for the lines (has no effect for great spells)",
        line_scale="The scale of the lines and dots in the image",
        arrow_scale="The scale of the arrows in the image",
    )
    @app_commands.rename(translation="name")
    async def name(
        self,
        interaction: discord.Interaction,
        translation: str,
        show_to_everyone: bool = False,
        palette: Palette = Palette.Classic,
        line_scale: SCALE_RANGE = DEFAULT_LINE_SCALE,
        arrow_scale: SCALE_RANGE = DEFAULT_ARROW_SCALE,
    ) -> None:
        """Display the stroke order of a pattern from its name (no number literals, for now)"""
        if translation.startswith("Bookkeeper's Gambit:"):
            mask = parse_mask(translation)
            if not mask:
                return await interaction.response.send_message("❌ Invalid Bookkeeper's Gambit, must not be empty and only contain the characters `v-`.", ephemeral=True)

            direction, pattern = generate_bookkeeper(mask)
            is_great = False
            name = "mask"
        elif (value := self.registry.translation_to_pattern.get(translation)) is None:
            return await interaction.response.send_message("❌ Unknown pattern.", ephemeral=True)
        else:
            direction, pattern, is_great, name = value

        await send_pattern(
            self.registry,
            interaction,
            name,
            translation,
            generate_image(direction, pattern, is_great, palette, line_scale, arrow_scale),
            not show_to_everyone,
        )
    
    @name.autocomplete("translation")
    async def name_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice]:
        if current.startswith("Bookkeeper's Gambit:"):
            if parse_mask(current) is not None: # intentionally "allow" blank mask for autocomplete, more intuitive imo
                return [app_commands.Choice(name=current, value=current)]
        return self.autocomplete.get(current.lower(), [])[:25]

class DecodeCog(commands.Cog):
    def __init__(self, bot: commands.Bot, registry: Registry) -> None:
        self.bot = bot
        self.registry = registry
    
    @app_commands.command()
    @app_commands.describe(
        data="The result of calling Reveal on your pattern list",
        show_to_everyone="Whether the result should be visible to everyone, or just you (to avoid spamming)",
    )
    async def decode(self, interaction: discord.Interaction, data: str, show_to_everyone: bool = False):
        """Decode a pattern list using hexdecode"""
        output = ""
        level = 0
        for pattern in revealparser.parse(data):
            for iota in massage_raw_pattern_list(pattern, self.registry):
                level = iota.preadjust(level)
                output += iota.print(level, False, self.registry) + "\n"
                level = iota.postadjust(level)
        
        if not output:
            return await interaction.response.send_message("❌ Invalid input.", ephemeral=True)

        await interaction.response.send_message(f"```\n{output}```", ephemeral=not show_to_everyone)

class BookCog(commands.GroupCog, name="book"):
    def __init__(self, bot: commands.Bot, registry: Registry) -> None:
        self.bot = bot
        self.registry = registry
        self.autocomplete = build_autocomplete(
            [(app_commands.Choice(name=title, value=title), names) for title, (_, _, names) in registry.page_title_to_url.items()]
        )
    
    @app_commands.command()
    @app_commands.describe(
        mod="The mod to link the home page for",
        show_to_everyone="Whether the result should be visible to everyone, or just you (to avoid spamming)",
        show_spoilers="Whether the link should have spoilers unblurred or not",
    )
    async def home(self, interaction: discord.Interaction, mod: ModName, show_to_everyone: bool = False, show_spoilers: bool = False) -> None:
        await interaction.response.send_message(build_book_url(mod, "", show_spoilers, True), ephemeral=not show_to_everyone)
    
    @app_commands.command()
    @app_commands.describe(
        page_title="The title of the page to link",
        show_to_everyone="Whether the result should be visible to everyone, or just you (to avoid spamming)",
        show_spoilers="Whether the link should have spoilers unblurred or not",
    )
    async def page(self, interaction: discord.Interaction, page_title: str, show_to_everyone: bool = False, show_spoilers: bool = False) -> None:
        """Get a link to the web book"""
        if not (value := self.registry.page_title_to_url.get(page_title)):
            return await interaction.response.send_message("❌ Unknown page.", ephemeral=True)

        mod, url, _ = value
        await interaction.response.send_message(build_book_url(mod, url, show_spoilers, True), ephemeral=not show_to_everyone)
    
    @page.autocomplete("page_title")
    async def page_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice]:
        return self.autocomplete.get(current.lower(), [])[:25]

class SourceCog(commands.GroupCog, name="source"):
    def __init__(self, bot: commands.Bot, registry: Registry) -> None:
        self.bot = bot
        self.registry = registry

        initial_choices = [
            (app_commands.Choice(name=translation, value=translation), [name])
            for name, translation in registry.name_to_translation.items()
        ]
        self.autocomplete = build_autocomplete(initial_choices)
    
    @app_commands.command()
    @app_commands.describe(
        mod="The mod to link the repository for",
        show_to_everyone="Whether the result should be visible to everyone, or just you (to avoid spamming)",
    )
    async def repo(self, interaction: discord.Interaction, mod: ModName, show_to_everyone: bool = False) -> None:
        await interaction.response.send_message(build_source_url(mod, ""), ephemeral=not show_to_everyone)
    
    @app_commands.command()
    @app_commands.describe(
        translation="The name of the pattern to link",
        show_to_everyone="Whether the result should be visible to everyone, or just you (to avoid spamming)",
    )
    @app_commands.rename(translation="name")
    async def pattern(self, interaction: discord.Interaction, translation: str, show_to_everyone: bool = False) -> None:
        """Get a link to the web book"""
        if not (value := self.registry.translation_to_path.get(translation)):
            return await interaction.response.send_message("❌ Unknown pattern.", ephemeral=True)

        mod, path, name = value
        filename: str = path.split("/")[-1]
        source_url = build_source_url(mod, path)

        await interaction.response.send_message(
            embed=discord.Embed(title=filename, url=source_url).set_author(name=f"{translation} ({name})"),
            ephemeral=not show_to_everyone,
        )
    
    @pattern.autocomplete("translation")
    async def pattern_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice]:
        return self.autocomplete.get(current.lower(), [])[:25]

class TagCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
    
    @app_commands.command()
    @app_commands.describe(
        tag="The name of the tag to show",
    )
    @app_commands.rename(tag="name")
    async def tag(self, interaction: discord.Interaction, tag: Tags):
        """Show a premade info message"""
        value: Tag = tag.value
        await interaction.response.send_message(**value._asdict())

def parse_mask(translation: str) -> str | None:
    mask = translation.removeprefix("Bookkeeper's Gambit:").lstrip().lower()
    if not all(c in "v-" for c in mask):
        return None
    return mask

def build_autocomplete(initial_choices: list[tuple[app_commands.Choice, list[str]]]) -> dict[str, list[app_commands.Choice]]:
    autocomplete: defaultdict[str, set[app_commands.Choice]] = defaultdict(set)
    for choice, other_names in initial_choices:
        for name in other_names + [choice.name]:
            name = name.lower()
            for i in range(len(name)):
                for j in range(i, len(name)):
                    autocomplete[name[i:j+1]].add(choice)
        autocomplete[""].add(choice)
    
    return {key: sorted(list(value), key=lambda c: c.name) for key, value in autocomplete.items()}

async def send_pattern(
    registry: Registry,
    interaction: discord.Interaction,
    name: str,
    translation: str,
    image: BytesIO,
    ephemeral: bool,
):
    mod, book_url = registry.name_to_url.get(name, (None, None))
    book_url = mod and book_url and build_book_url(mod, book_url, False, False)

    embed = discord.Embed(
        title=translation,
        url=book_url,
        description=registry.name_to_args.get(name),
    ).set_image(url="attachment://pattern.png")
    if mod:
        mod_info = MOD_INFO[mod]
        embed.set_author(name=mod, icon_url=mod_info.icon_url, url=mod_info.mod_url)

    await interaction.response.send_message(
        embed=embed,
        file=discord.File(image, filename="pattern.png"),
        ephemeral=ephemeral,
    )

def build_book_url(mod: ModName, url: str, show_spoilers: bool, escape: bool) -> str:
    book_url = f"{MOD_INFO[mod].book_url}{'?nospoiler' if show_spoilers else ''}{url}"
    if escape:
        book_url = f"<{book_url}>"
    if show_spoilers:
        book_url = f"||{book_url}||"
    return book_url

def build_source_url(mod: ModName, path: str):
    return f"{MOD_INFO[mod].source_url}{'blob/main/' if path else ''}{path}"

async def main():
    load_dotenv(".env")
    token = os.environ.get("TOKEN")
    if not token:
        raise Exception("TOKEN not found in .env")

    registry = build_registry()

    intents = discord.Intents.default()
    bot = commands.Bot(command_prefix=commands.when_mentioned, intents=intents)
    
    discord.utils.setup_logging(level=logging.INFO) # WHY ISN'T THIS ENABLED BY DEFAULT
    async with bot:
        await bot.add_cog(MessageCommandsCog(bot))
        await bot.add_cog(EventsCog(bot))
        await bot.add_cog(TagCog(bot))
        await bot.add_cog(PatternCog(bot, registry))
        await bot.add_cog(DecodeCog(bot, registry))
        await bot.add_cog(SourceCog(bot, registry))
        await bot.add_cog(BookCog(bot, registry))
        await bot.start(token)

if __name__ == "__main__":
    asyncio.run(main())
