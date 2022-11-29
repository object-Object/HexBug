import discord
from discord.utils import MISSING

TIMEOUT = 120


def buildShowOrDeleteButton(
    show_to_everyone: bool,
    interaction: discord.Interaction,
    content: str = "",
    embed: discord.Embed = MISSING,
    file: discord.File = MISSING,
) -> discord.ui.View:
    return (
        DeleteButton(interaction=interaction)
        if show_to_everyone
        else ShowToEveryoneButton(interaction=interaction, content=content, embed=embed, file=file)
    )


class _BaseButton(discord.ui.View):
    def __init__(self, interaction: discord.Interaction):
        super().__init__(timeout=TIMEOUT)
        self.interaction = interaction

    async def on_timeout(self) -> None:
        await self.disable_buttons()

    async def delete_message(self) -> None:
        await self.interaction.delete_original_response()
        self.stop()

    async def disable_buttons(self) -> None:
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                item.disabled = True
        await self.interaction.edit_original_response(view=self)


class ShowToEveryoneButton(_BaseButton):
    def __init__(
        self,
        interaction: discord.Interaction,
        content: str = "",
        embed: discord.Embed = MISSING,
        file: discord.File = MISSING,
    ):
        super().__init__(interaction)
        self.content = content
        self.embed = embed
        self.file = file

    @discord.ui.button(label="Show to everyone", style=discord.ButtonStyle.gray)
    async def button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.file is not MISSING:
            self.file.reset()

        assert (command := self.interaction.command)
        await interaction.response.send_message(
            content=f"{interaction.user.mention} used `/{command.qualified_name}`\n{self.content}",
            embed=self.embed,
            file=self.file,
            allowed_mentions=discord.AllowedMentions.none(),
            view=DeleteButton(interaction=interaction),
        )
        await self.delete_message()


class DeleteButton(_BaseButton):
    @discord.ui.button(emoji="🗑️", style=discord.ButtonStyle.gray)
    async def button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.interaction.user:
            return await interaction.response.send_message(
                f"Only {self.interaction.user.mention} can do that.",
                ephemeral=True,
            )
        await self.delete_message()
