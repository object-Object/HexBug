from io import BytesIO
from typing import Any

import humanize
from discord import Attachment, Color, File, Interaction, app_commands
from discord.app_commands import Range
from discord.ext.commands import GroupCog
from discord.ui import (
    ActionRow,
    Container,
    File as FileComponent,
    LayoutView,
    TextDisplay,
)
from discord.utils import MISSING
from lark import LarkError

from HexBug.core.cog import HexBugCog
from HexBug.core.exceptions import InvalidInputError
from HexBug.parser.reveal import parse_reveal
from HexBug.utils.discord.visibility import (
    Visibility,
    VisibilityOption,
    add_visibility_buttons,
)

MAX_FILE_SIZE = 32 * 1024

MAX_CONTENT_LENGTH = 4000

ATTACHMENT_NAME = "decoded.hexpattern"

TabWidthOption = Range[int, 1, 16]


class DecodeCog(HexBugCog, GroupCog, group_name="decode"):
    @app_commands.command()
    async def text(
        self,
        interaction: Interaction,
        text: str,
        tab_width: TabWidthOption = 4,
        visibility: VisibilityOption = Visibility.PRIVATE,
    ):
        await self._decode(interaction, text, tab_width, visibility)

    @app_commands.command()
    async def file(
        self,
        interaction: Interaction,
        file: Attachment,
        tab_width: TabWidthOption = 4,
        visibility: VisibilityOption = Visibility.PRIVATE,
    ):
        if file.size > MAX_FILE_SIZE:
            raise InvalidInputError(
                f"File is too large (max: {humanize.naturalsize(MAX_FILE_SIZE, binary=True)}).",
                value=f"{file.filename} ({humanize.naturalsize(file.size, binary=True)})",
            )

        try:
            text = (await file.read()).decode()
        except UnicodeDecodeError as e:
            raise InvalidInputError(
                "Unable to decode file as UTF-8.",
                value=file.filename,
            ) from e

        await self._decode(interaction, text, tab_width, visibility)

    async def _decode(
        self,
        interaction: Interaction,
        text: str,
        tab_width: int,
        visibility: Visibility,
    ):
        try:
            iota = parse_reveal(text)
        except LarkError as e:
            raise InvalidInputError("Failed to parse input.", fields=[]).add_field(
                name="Reason",
                value=f"```\n{e}\n```",
                inline=False,
            )

        output = self.bot.iota_printer.pretty_print(iota, indent=" " * tab_width)

        view = LayoutView()

        content_template = "```\n{}\n```"
        content = content_template.format(output)

        if len(content) <= MAX_CONTENT_LENGTH:
            file_contents = None
            view.add_item(TextDisplay(content))
        else:
            too_long_error = "Output truncated due to length limits."
            ellipses = "\n..."
            max_output_length = (
                MAX_CONTENT_LENGTH
                - len(content_template)
                - len(too_long_error)
                - len(ellipses)
            )

            truncated_output = output[:max_output_length].rsplit("\n", 1)[0] + ellipses
            file_contents = output.encode()

            view.add_item(TextDisplay(content_template.format(truncated_output)))

            view.add_item(
                Container[Any](
                    TextDisplay(too_long_error),
                    FileComponent(f"attachment://{ATTACHMENT_NAME}"),
                    accent_colour=Color.red(),
                )
            )

        # TODO: make this a function

        row = ActionRow[Any]()
        view.add_item(row)

        async def send_as_public(i: Interaction):
            row.clear_items()
            add_visibility_buttons(
                row,
                i,
                Visibility.PUBLIC,
                command=interaction.command,
                show_usage=True,
            )
            await i.response.send_message(
                view=view,
                file=File(BytesIO(file_contents), ATTACHMENT_NAME)
                if file_contents
                else MISSING,
            )

        add_visibility_buttons(
            row,
            interaction,
            visibility,
            command=interaction.command,
            show_usage=False,
            send_as_public=send_as_public,
        )

        await interaction.response.send_message(
            view=view,
            ephemeral=visibility.ephemeral,
            file=File(BytesIO(file_contents), ATTACHMENT_NAME)
            if file_contents
            else MISSING,
        )
