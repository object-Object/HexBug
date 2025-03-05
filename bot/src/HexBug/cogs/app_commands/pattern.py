from discord import Interaction, app_commands
from discord.ext.commands import GroupCog

from HexBug.core.cog import HexBugCog
from HexBug.utils.discord.transformers import PatternInfoOption
from HexBug.utils.discord.visibility import MessageVisibility


class PatternCog(HexBugCog, GroupCog, group_name="pattern"):
    @app_commands.command()
    @app_commands.rename(pattern="name")
    async def name(
        self,
        interaction: Interaction,
        pattern: PatternInfoOption,
        visibility: MessageVisibility = "private",
    ):
        # TODO: implement
        await interaction.response.send_message(str(pattern), ephemeral=True)
