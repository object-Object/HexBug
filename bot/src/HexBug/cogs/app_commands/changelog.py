import re
from dataclasses import dataclass, field

from discord import Embed, Interaction, SelectOption, app_commands

from HexBug.core.cog import HexBugCog
from HexBug.resources import load_resource
from HexBug.ui.views.embed_switcher import EmbedSwitcherView
from HexBug.utils.discord.visibility import Visibility, VisibilityOption

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
            line = line.rstrip()

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

        await EmbedSwitcherView(
            user=interaction.user,
            command=interaction.command,
            embeds=(entry.embed for entry in self._changelog),
            options=(
                SelectOption(label=entry.version, description=entry.date)
                for entry in self._changelog
            ),
        ).send(interaction, visibility)
