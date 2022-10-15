import asyncio
from collections import defaultdict
import os
import discord
from discord import app_commands
from discord.ext import commands
import revealparser
from hexast import PatternRegistry, Direction, _parse_unknown_pattern, UnknownPattern, massage_raw_pattern_list
from buildpatterns import build_registry
from dotenv import load_dotenv
from generate_image import generate_image

default_line_scale = 6
default_arrow_scale = 2

class MessageCommandsCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Logged in as {self.bot.user}")

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

class PatternCog(commands.GroupCog, name="pattern"):
    def __init__(self, bot: commands.Bot, registry: PatternRegistry) -> None:
        self.bot = bot
        self.registry = registry
        self.autocomplete = build_autocomplete([
            (app_commands.Choice(name=translation, value=translation), [name])
            for name, translation in registry.name_to_translation.items()
            if translation not in ["Bookkeeper's Gambit", "Numerical Reflection"]
        ])

        super().__init__()
    
    @app_commands.command()
    @app_commands.describe(
        direction="The starting direction of the pattern",
        pattern='The angle signature of the pattern (eg. aqaawde) — type "-" to leave blank',
        line_scale="The scale of the lines and dots in the image",
        arrow_scale="The scale of the arrows in the image",
    )
    async def raw(
        self,
        interaction: discord.Interaction,
        direction: Direction,
        pattern: str,
        line_scale: app_commands.Range[float, 0.1] = default_line_scale,
        arrow_scale: app_commands.Range[float, 0.1] = default_arrow_scale,
    ) -> None:
        """Display the stroke order of a pattern from its direction and angle signature"""
        if pattern in ["-", '"-"']:
            pattern = ""
        elif not all(c in "aqwed" for c in pattern):
            return await interaction.response.send_message(
                "❌ Invalid angle signature, must only contain the characters `aqwed`.",
                ephemeral=True,
            )
        
        pattern_iota = _parse_unknown_pattern(UnknownPattern(direction, pattern), self.registry)

        await interaction.response.send_message(
            f"**{pattern_iota.localize(self.registry)}**",
            file=discord.File(generate_image(direction, pattern, False, line_scale, arrow_scale), filename="pattern.png")
        )

    @app_commands.command()
    @app_commands.describe(
        translation="The name of the pattern",
        line_scale="The scale of the lines and dots in the image",
        arrow_scale="The scale of the arrows in the image",
    )
    @app_commands.rename(translation="name")
    async def name(
        self,
        interaction: discord.Interaction,
        translation: str,
        line_scale: app_commands.Range[float, 0.1] = default_line_scale,
        arrow_scale: app_commands.Range[float, 0.1] = default_arrow_scale,
    ) -> None:
        """Display the stroke order of a pattern from its name (no number literals or Bookkeepers)"""
        if (value := self.registry.translation_to_pattern.get(translation)) is None:
            return await interaction.response.send_message("❌ Unknown pattern.", ephemeral=True)
        
        direction, pattern, is_great = value
        await interaction.response.send_message(
            f"**{translation}**",
            file=discord.File(generate_image(direction, pattern, is_great, line_scale, arrow_scale), filename="pattern.png")
        )
    
    @name.autocomplete("translation")
    async def name_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice]:
        return self.autocomplete.get(current, [])[:25]

class DecodeCog(commands.Cog):
    def __init__(self, bot: commands.Bot, registry: PatternRegistry) -> None:
        self.bot = bot
        self.registry = registry
    
    @app_commands.command()
    @app_commands.describe(
        data="The result of calling Reveal on your pattern list",
        show_to_everyone="Whether the result should be visible to everyone, or just you (to avoid spamming)"
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
            return await interaction.response.send_message("❌ Invalid data.", ephemeral=True)

        await interaction.response.send_message(f"```\n{output}```", ephemeral=not show_to_everyone)

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

async def main():
    load_dotenv(".env")
    token = os.environ.get("TOKEN")
    if not token:
        raise Exception("TOKEN not found in .env")

    registry = build_registry()

    intents = discord.Intents.default()
    bot = commands.Bot(command_prefix=commands.when_mentioned, intents=intents)

    async with bot:
        await bot.add_cog(MessageCommandsCog(bot))
        await bot.add_cog(PatternCog(bot, registry))
        await bot.add_cog(DecodeCog(bot, registry))
        await bot.start(token)

if __name__ == "__main__":
    asyncio.run(main())
