import logging
from itertools import chain
from typing import Iterable

import discord
from aiohttp import ClientResponseError
from discord import app_commands
from discord.ext import commands, tasks
from semver.version import Version

from ..utils import modrinth
from ..utils.buttons import get_full_command
from ..utils.commands import HexBugBot
from ..utils.mods import APIMod, Mod, RegistryMod


def _on_fetch_error(mod: Mod, resp_status: int, resp_message: str):
    message = f"{mod.value.name}: [{resp_status}] {resp_message}"
    logging.error("Failed to fetch version for " + message)
    return message


class EventsCog(commands.Cog):
    def __init__(self, bot: HexBugBot) -> None:
        self.bot = bot
        self.version_cache = {mod: Version.parse(mod.value.version) for mod in chain(RegistryMod, APIMod)}

    # return an iterable to make it easy to optionally insert into a list
    async def _check_update(self, mod: Mod, latest: str) -> Iterable[str]:
        latest_ver = Version.parse(latest)
        # walksanator pls
        if latest_ver <= self.version_cache[mod] or (mod is RegistryMod.HexTweaks and latest == "3.2.3"):
            return []

        self.version_cache[mod] = latest_ver

        message = f"{mod.value.name} {latest} (from {mod.value.version})"
        logging.warning(f"Update available: {message}")
        return [message]

    # title may have a str.format placeholder for an "s" if there's more than one message
    async def _log_messages(self, title: str, messages: list[str]):
        if joined := "\n".join(messages):
            f_title = title.format(s=("s" if len(messages) > 1 else ""))
            await self.bot.log_webhook.send(f"{f_title}\n{joined}")

    @commands.Cog.listener()
    async def on_ready(self):
        logging.getLogger("bot").info(f"Logged in as {self.bot.user}")
        self.check_for_updates.start()

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        # log commands in case something breaks and i need to see how
        if interaction.type == discord.InteractionType.application_command and isinstance(
            command := interaction.command, app_commands.Command
        ):
            logging.getLogger("bot").debug(
                f"Command executed: {get_full_command(interaction, command, truncate=False)}"
            )

    @tasks.loop(hours=1)
    async def check_for_updates(self):
        update_messages = []
        error_messages = []

        # check registry mods by fetching from Modrinth
        for mod in RegistryMod:
            if mod.value.modrinth_slug is None:
                continue

            # TODO: this is basically the same block as below, refactor it out
            try:
                versions = await modrinth.get_versions(self.bot.session, mod.value.modrinth_slug)
            except ClientResponseError as e:
                error_messages.append(_on_fetch_error(mod, e.status, e.message))
                continue
            latest = versions[0]["version_number"]
            update_messages.extend(await self._check_update(mod, latest))

        # check API mods by querying the API
        for mod in APIMod:
            try:
                versions = await mod.value.api.get_versions(self.bot.session)
            except ClientResponseError as e:
                if not (500 <= e.status < 600):
                    error_messages.append(_on_fetch_error(mod, e.status, e.message))
                continue
            latest = versions["versions"][0]["id"]
            update_messages.extend(await self._check_update(mod, latest))

        # if there's any new updates or any errors, log them
        await self._log_messages("**Update{s} available!**", update_messages)
        await self._log_messages("**Error{s} while checking for updates!**", error_messages)


async def setup(bot: HexBugBot) -> None:
    await bot.add_cog(EventsCog(bot))
