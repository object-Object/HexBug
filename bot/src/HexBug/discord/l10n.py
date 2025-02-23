import logging
import re
from contextlib import ExitStack
from typing import Any

from discord import Interaction, Locale
from discord.app_commands import (
    TranslationContextLocation,
    TranslationContextTypes,
    Translator,
    locale_str,
)
from fluent.runtime import FluentLocalization, FluentResourceLoader

from HexBug.resources import load_resource_dir

logger = logging.getLogger(__name__)

_SEPARATOR_PATTERN = re.compile(r"[ _-]+")


class HexBugTranslator(Translator):
    async def load(self) -> None:
        self.exit_stack = ExitStack()

        path = self.exit_stack.enter_context(load_resource_dir("l10n"))
        loader = FluentResourceLoader(path.as_posix() + "/{locale}")

        self.l10n = {
            locale: FluentLocalization(
                locales=[locale.value, "en-US"],
                resource_ids=["main.ftl"],
                resource_loader=loader,
            )
            for locale in Locale
        }

    async def unload(self) -> None:
        self.exit_stack.close()

    async def translate(
        self,
        string: locale_str,
        locale: Locale,
        context: TranslationContextTypes,
    ) -> str | None:
        match string.extras:
            case {"id": str(msg_id)}:
                pass
            case _:
                match context.location:
                    case TranslationContextLocation.command_description:
                        msg_id = command_description_id(context.data.qualified_name)
                    case TranslationContextLocation.parameter_description:
                        msg_id = parameter_description_id(
                            command=context.data.command.qualified_name,
                            parameter=context.data.name,
                        )
                    case _:
                        msg_id = string.message

        result = self.l10n[locale].format_value(msg_id, string.extras)
        if result == msg_id:
            return string.message
        return result


async def translate_text(interaction: Interaction, key: str, **kwargs: Any):
    if interaction.command is None:
        raise ValueError(
            "Attempted to translate command text when interaction.command is None"
        )

    msg_id = command_text_id(interaction.command.qualified_name, key)
    result = await interaction.translate(locale_str(msg_id, **kwargs))

    if result is None:
        logger.warning(f"Failed to translate string: {msg_id}")
        return msg_id

    return result


def command_description_id(command: str):
    command = _format_identifier(command)
    return f"{command}_description"


def parameter_description_id(command: str | None, parameter: str):
    command = _format_identifier(command or "common")
    parameter = _format_identifier(parameter)
    return f"{command}_parameter-description_{parameter}"


def command_text_id(command: str, key: str):
    command = _format_identifier(command)
    return f"{command}_text_{key}"


def _format_identifier(command: str):
    return _SEPARATOR_PATTERN.sub("-", command).replace("/", "")
