import logging
from dataclasses import dataclass
from datetime import datetime

from discord import CustomActivity, Emoji, Intents, Interaction
from discord.app_commands import AppCommandContext, AppInstallationType
from discord.ext import commands
from discord.ext.commands import Bot, Context, NoEntryPointError

from HexBug import cogs
from HexBug.common import VERSION
from HexBug.utils.imports import iter_modules

from .emoji import CustomEmoji
from .env import HexBugEnv
from .translator import HexBugTranslator
from .tree import HexBugCommandTree

logger = logging.getLogger(__name__)

COGS_MODULE = cogs.__name__


@dataclass
class HexBugBot(Bot):
    env: HexBugEnv

    def __post_init__(self):
        super().__init__(
            command_prefix=commands.when_mentioned,
            intents=Intents.default(),
            activity=CustomActivity(f"v{VERSION}"),
            allowed_installs=AppInstallationType(guild=True, user=True),
            allowed_contexts=AppCommandContext(
                guild=True, dm_channel=True, private_channel=True
            ),
            tree_cls=HexBugCommandTree,
        )
        self.start_time = datetime.now()
        self._custom_emoji = dict[CustomEmoji, Emoji]()

    @classmethod
    def of(cls, interaction: Interaction):
        bot = interaction.client
        assert isinstance(bot, cls)
        return bot

    async def load(self):
        await self._load_translator()
        await self._load_cogs()

    async def _load_translator(self):
        logger.info("Loading translator")
        await self.tree.set_translator(HexBugTranslator())

    async def _load_cogs(self):
        for cog in iter_modules(cogs, skip_internal=True):
            try:
                logger.info(f"Loading extension: {cog}")
                await self.load_extension(cog)
            except NoEntryPointError:
                logger.warning(f"No entry point found: {cog}")
        logger.info("Loaded cogs: " + ", ".join(self.cogs.keys()))

    async def fetch_custom_emojis(self):
        logger.info("Fetching custom emojis")

        application_emojis = {
            emoji.name: emoji for emoji in await self.fetch_application_emojis()
        }

        self._custom_emoji.clear()
        for custom_emoji in CustomEmoji:
            if emoji := application_emojis.get(custom_emoji.name):
                self._custom_emoji[custom_emoji] = emoji
            else:
                logger.warning(
                    f"Failed to find custom emoji (try running `sync emoji` command): {custom_emoji.name}"
                )

    async def sync_custom_emojis(self):
        logger.info("Syncing/uploading custom emojis")

        self._custom_emoji.clear()

        for emoji in await self.fetch_application_emojis():
            await emoji.delete()

        for custom_emoji in CustomEmoji:
            self._custom_emoji[custom_emoji] = await self.create_application_emoji(
                name=custom_emoji.name,
                image=custom_emoji.load_image(),
            )

    def get_custom_emoji(self, custom_emoji: CustomEmoji) -> Emoji:
        emoji = self._custom_emoji.get(custom_emoji)
        if emoji is None:
            raise ValueError(f"Failed to find custom emoji: {custom_emoji.name}")
        return emoji


type HexBugContext = Context[HexBugBot]

type HexBugInteraction = Interaction[HexBugBot]
