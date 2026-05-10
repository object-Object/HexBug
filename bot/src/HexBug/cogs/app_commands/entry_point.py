from discord import Interaction

from HexBug.core.cog import HexBugCog
from HexBug.utils.discord.entry_points import entry_point_command


class EntryPointCog(HexBugCog):
    @entry_point_command(name="entry-point")
    async def entry_point(self, interaction: Interaction):
        await interaction.response.launch_activity()
