import itertools
import logging
from datetime import datetime
from typing import Iterator

from discord import AppCommandType, CustomActivity, Emoji, Intents, Interaction, Locale
from discord.app_commands import (
    AppCommandContext,
    AppInstallationType,
    Command,
    ContextMenu,
    Group,
    TranslationContext,
    TranslationContextLocation,
    TranslationContextTypes,
    locale_str,
)
from discord.ext import commands
from discord.ext.commands import Bot, Context, NoEntryPointError

from HexBug import cogs
from HexBug.common import VERSION
from HexBug.data.mods import Modloader
from HexBug.data.registry import HexBugRegistry
from HexBug.parser.pretty_print import IotaPrinter
from HexBug.utils.imports import iter_modules

from .emoji import CustomEmoji
from .env import HexBugEnv
from .translator import HexBugTranslator
from .tree import HexBugCommandTree

logger = logging.getLogger(__name__)

COGS_MODULE = cogs.__name__


class HexBugBot(Bot):
    env: HexBugEnv
    registry: HexBugRegistry
    should_run: bool
    start_time: datetime
    iota_printer: IotaPrinter
    _custom_emoji: dict[CustomEmoji, Emoji]
    _failed_translations: set[Locale]

    # late-initialized
    _translator: HexBugTranslator

    def __init__(self, env: HexBugEnv, registry: HexBugRegistry, run: bool):
        super().__init__(
            command_prefix=commands.when_mentioned,
            intents=Intents.default(),
            activity=self._get_activity(env),
            allowed_installs=AppInstallationType(guild=True, user=True),
            allowed_contexts=AppCommandContext(
                guild=True, dm_channel=True, private_channel=True
            ),
            tree_cls=HexBugCommandTree,
        )
        self.env = env
        self.registry = registry
        self.should_run = run
        self.start_time = datetime.now()
        self.iota_printer = IotaPrinter(self.registry)
        self._custom_emoji = {}
        self._failed_translations = set()

    @classmethod
    def of(cls, interaction: Interaction):
        bot = interaction.client
        assert isinstance(bot, cls)
        return bot

    @classmethod
    def registry_of(cls, interaction: Interaction):
        return cls.of(interaction).registry

    @classmethod
    def _get_activity(cls, env: HexBugEnv):
        text = f"v{VERSION}"
        match env.environment:
            case "dev":
                text += " (local development)"
            case "beta":
                if env.deployment:
                    text += f" @ {env.deployment.commit_sha[:8]}"
                else:
                    text += " @ (unknown)"
            case "prod":
                pass
        return CustomActivity(text)

    @property
    def failed_translations(self):
        return self._failed_translations

    async def load(self):
        await self._load_translator()
        await self._load_cogs()
        await self._check_translations()

    async def _load_translator(self):
        logger.info("Loading translator")
        self._translator = HexBugTranslator()
        await self.tree.set_translator(self._translator)

    async def _load_cogs(self):
        for cog in iter_modules(cogs, skip_internal=True):
            try:
                logger.info(f"Loading extension: {cog}")
                await self.load_extension(cog)
            except NoEntryPointError:
                logger.warning(f"No entry point found: {cog}")
        logger.info("Loaded cogs: " + ", ".join(self.cogs.keys()))

    async def _check_translations(self):
        self._failed_translations.clear()
        for locale in self._translator.l10n.keys():
            for context in self._walk_tree_translations():
                await self._check_translation(locale, context)

    def _walk_tree_translations(self) -> Iterator[TranslationContextTypes]:
        for command in itertools.chain(
            self.tree.walk_commands(type=AppCommandType.chat_input),
            self.tree.walk_commands(type=AppCommandType.user),
            self.tree.walk_commands(type=AppCommandType.message),
        ):
            match command:
                case Command():
                    yield TranslationContext(
                        TranslationContextLocation.command_name, command
                    )
                    yield TranslationContext(
                        TranslationContextLocation.command_description, command
                    )
                    for parameter in command.parameters:
                        yield TranslationContext(
                            TranslationContextLocation.parameter_name, parameter
                        )
                        yield TranslationContext(
                            TranslationContextLocation.parameter_description, parameter
                        )

                case Group():
                    yield TranslationContext(
                        TranslationContextLocation.group_name, command
                    )
                    yield TranslationContext(
                        TranslationContextLocation.group_description, command
                    )

                case ContextMenu():
                    yield TranslationContext(
                        TranslationContextLocation.command_name, command
                    )

    async def _check_translation(
        self,
        locale: Locale,
        context: TranslationContextTypes,
    ):
        string = locale_str("__canary")
        result = await self._translator.translate(
            string, locale, context, fallback=False
        )
        if result is None:
            self._failed_translations.add(locale)
            logger.warning(
                f"Failed to translate {context.location.name} to {locale.value}: {context.data.name}"
            )
        elif result == string.message:
            self._failed_translations.add(locale)
            logger.warning(
                f"Missing translation for {locale.value}: {self._translator.get_msg_id(string, context)}"
            )
        else:
            match context.location:
                case (
                    TranslationContextLocation.command_name
                    | TranslationContextLocation.group_name
                    | TranslationContextLocation.parameter_name
                ):
                    max_length = 32
                case (
                    TranslationContextLocation.command_description
                    | TranslationContextLocation.group_description
                    | TranslationContextLocation.parameter_description
                    | TranslationContextLocation.choice_name
                ):
                    max_length = 100
                case _:
                    max_length = None
            if max_length and len(result) > max_length:
                self._failed_translations.add(locale)
                logger.warning(
                    f"Translation for {locale.value} is too long: {self._translator.get_msg_id(string, context)}"
                )

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

    def get_modloader_emoji(self, modloader: Modloader) -> Emoji:
        return self.get_custom_emoji(CustomEmoji.from_modloader(modloader))


type HexBugContext = Context[HexBugBot]

type HexBugInteraction = Interaction[HexBugBot]
