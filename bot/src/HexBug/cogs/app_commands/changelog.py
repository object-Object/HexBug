import re
from dataclasses import dataclass, field
from typing import Any

from discord import Embed, Interaction, SelectOption, app_commands
from discord.ui import Select

from HexBug.core.cog import HexBugCog
from HexBug.resources import load_resource
from HexBug.utils.discord.components import update_indexed_select_menu
from HexBug.utils.discord.visibility import (
    MessageContents,
    Visibility,
    VisibilityOption,
)

_VERSION_PATTERN = re.compile(
    r"## (?:`(?P<version>[^`]+)` - (?P<date>\d{4}-\d{2}-\d{2})|(?P<unknown>.+))"
)


@dataclass(kw_only=True)
class ChangelogEntry:
    version: str
    date: str | None
    body: str

    def __post_init__(self):
        self.embed = Embed(
            description=f"## {self.version}\n{self.body}",
        ).set_footer(
            text=self.date,
        )


@dataclass
class ChangelogEntryBuilder:
    version: str
    date: str | None = None
    body: list[str] = field(default_factory=lambda: [])

    def build(self):
        return ChangelogEntry(
            version=self.version,
            date=self.date,
            body="\n".join(self.body),
        )


@dataclass(eq=False)
class ChangelogCog(HexBugCog):
    def __post_init__(self):
        self._changelog = list[ChangelogEntry]()

        try:
            changelog = load_resource("CHANGELOG.md")
        except Exception:
            return

        builder = None

        for line in changelog.splitlines():
            line = line.strip()

            if match := _VERSION_PATTERN.match(line):
                if builder:
                    self._changelog.append(builder.build())

                if version := match["version"]:
                    builder = ChangelogEntryBuilder(version, match["date"])
                else:
                    builder = ChangelogEntryBuilder(match["unknown"])

            elif builder and line:
                builder.body.append(line)

        if builder:
            self._changelog.append(builder.build())

    @app_commands.command()
    async def changelog(
        self,
        interaction: Interaction,
        visibility: VisibilityOption = Visibility.PRIVATE,
    ):
        if not self._changelog:
            raise NotImplementedError

        select = Select[Any](
            options=[
                SelectOption(
                    label=entry.version,
                    value=str(i),
                    description=entry.date,
                    default=i == 0,
                )
                for i, entry in enumerate(self._changelog)
            ],
            row=2,
        )

        contents = MessageContents(
            command=interaction.command,
            embed=self._changelog[0].embed,
            items=[select],
        )

        async def callback(interaction: Interaction):
            index = update_indexed_select_menu(select)[0]
            contents.embed = self._changelog[index].embed
            await interaction.response.edit_message(
                embed=contents.embed,
                view=select.view,
            )

        select.callback = callback

        await contents.send_response(interaction, visibility)
