from dataclasses import dataclass

from discord import Interaction, SelectOption, app_commands

from HexBug.core.cog import HexBugCog
from HexBug.resources import load_resource
from HexBug.ui.views.paginated import SelectPaginatedView
from HexBug.utils.changelog import parse_changelog
from HexBug.utils.discord.visibility import Visibility, VisibilityOption


@dataclass(eq=False)
class ChangelogCog(HexBugCog):
    def __post_init__(self):
        try:
            changelog = load_resource("CHANGELOG.md")
        except Exception:
            pass
        else:
            self._changelog = parse_changelog(changelog)

    @app_commands.command()
    async def changelog(
        self,
        interaction: Interaction,
        visibility: VisibilityOption = Visibility.PRIVATE,
    ):
        if not self._changelog:
            raise NotImplementedError

        await SelectPaginatedView(
            user=interaction.user,
            command=interaction.command,
            embeds=(entry.embed for entry in self._changelog),
            options=(
                SelectOption(label=entry.version, description=entry.date)
                for entry in self._changelog
            ),
        ).send(interaction, visibility)
