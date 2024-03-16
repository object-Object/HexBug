from io import BytesIO

import discord
from discord import app_commands
from discord.ext import commands
from lark import LarkError

from HexBug.hexdecode.pretty_print import IotaPrinter

from ..hexdecode import revealparser
from ..utils.buttons import build_show_or_delete_button
from ..utils.commands import HexBugBot


class DecodeCog(commands.GroupCog, name="decode"):
    def __init__(self, bot: HexBugBot) -> None:
        self.bot = bot
        self.registry = bot.registry
        self.printer = IotaPrinter(self.registry)

    @app_commands.command()
    @app_commands.describe(
        data="The result of calling Reveal on your pattern list",
        tab_width="The amount of spaces per indentation level",
        show_to_everyone="Whether the result should be visible to everyone, or just you (to avoid spamming)",
    )
    async def text(
        self,
        interaction: discord.Interaction,
        data: str,
        tab_width: app_commands.Range[int, 1, 16] = 4,
        show_to_everyone: bool = False,
    ):
        """Decode a pattern list using hexdecode"""
        await self._decode(interaction, data, tab_width, show_to_everyone)

    @app_commands.command()
    @app_commands.describe(
        file="The result of calling Reveal on your pattern list",
        tab_width="The amount of spaces per indentation level",
        show_to_everyone="Whether the result should be visible to everyone, or just you (to avoid spamming)",
    )
    async def upload(
        self,
        interaction: discord.Interaction,
        file: discord.Attachment,
        tab_width: app_commands.Range[int, 1, 16] = 4,
        show_to_everyone: bool = False,
    ):
        """Decode the contents of a file using hexdecode"""
        if not file.filename.endswith(".txt"):
            return await interaction.followup.send(
                "❌ Only `.txt` files are supported.",
                ephemeral=True,
            )

        if file.size > 25_000:
            return await interaction.followup.send(
                "❌ File is too large.",
                ephemeral=True,
            )

        try:
            data = (await file.read()).decode()
        except UnicodeDecodeError:
            return await interaction.followup.send(
                "❌ Failed to decode file. Only plain text is supported.",
                ephemeral=True,
            )

        await self._decode(interaction, data, tab_width, show_to_everyone)

    async def _decode(
        self,
        interaction: discord.Interaction,
        data: str,
        tab_width: int,
        show_to_everyone: bool,
    ):
        await interaction.response.defer(ephemeral=not show_to_everyone, thinking=True)

        try:
            iota = revealparser.parse(data)
        except LarkError as e:
            return await interaction.followup.send(
                f"❌ Failed to parse input. ```\n{e}\n```",
                ephemeral=True,
            )

        output = self.printer.pretty_print(iota, indent=" " * tab_width)
        if not output:
            return await interaction.followup.send(
                "❌ Failed to print iota.",
                ephemeral=True,
            )

        content = f"```\n{output}```"
        if len(content) > 2000:
            content = "⚠️ Result is too long to display. See attached file."
            file = discord.File(BytesIO(output.encode("utf-8")), filename="decoded.txt")
            return await interaction.followup.send(
                content,
                ephemeral=not show_to_everyone,
                file=file,
                view=build_show_or_delete_button(
                    show_to_everyone, interaction, content=content, file=file
                ),
            )

        await interaction.followup.send(
            content,
            ephemeral=not show_to_everyone,
            view=build_show_or_delete_button(
                show_to_everyone, interaction, content=content
            ),
        )


async def setup(bot: HexBugBot) -> None:
    await bot.add_cog(DecodeCog(bot))
