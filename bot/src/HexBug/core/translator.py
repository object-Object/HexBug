import logging
import re
from contextlib import ExitStack
from typing import Any

from discord import Interaction, Locale
from discord.app_commands import (
    Command,
    ContextMenu,
    Group,
    Parameter,
    TranslationContextLocation,
    TranslationContextTypes,
    Translator,
    locale_str,
)
from fluent.runtime import FluentLocalization, FluentResourceLoader
from fluent.runtime.types import FluentNone

from HexBug.resources import load_resource_dir
from HexBug.utils.discord.commands import AnyCommand

logger = logging.getLogger(__name__)

_SEPARATOR_PATTERN = re.compile(r"[ _-]+")


type TranslationCommand = AnyCommand | ContextMenu


class HexBugTranslator(Translator):
    async def load(self) -> None:
        self.exit_stack = ExitStack()

        path = self.exit_stack.enter_context(load_resource_dir("lang"))
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
        msg_id = self._get_msg_id(string, context)
        result = format_value_with_attributes(self.l10n[locale], msg_id, string.extras)
        if result == msg_id:
            return string.message
        return result

    def _get_msg_id(self, string: locale_str, context: TranslationContextTypes) -> str:
        match string.extras:
            case {"id": str(msg_id)}:
                return msg_id
            case _:
                pass

        match context.location:
            case TranslationContextLocation.command_name:
                return command_id(context.data)

            case TranslationContextLocation.command_description:
                return command_description_id(context.data)

            case TranslationContextLocation.group_name:
                return group_id(context.data)

            case TranslationContextLocation.group_description:
                return group_description_id(context.data)

            case TranslationContextLocation.parameter_name:
                return parameter_id(context.data)

            case TranslationContextLocation.parameter_description:
                return parameter_description_id(context.data)

            case _:
                return string.message


async def translate_text(interaction: Interaction, key: str, **kwargs: Any):
    if interaction.command is None:
        raise ValueError(
            "Attempted to translate command text when interaction.command is None"
        )

    msg_id = command_text_id(interaction.command, key)
    return await _translate_or_warn(interaction, msg_id, **kwargs)


async def translate_group_text(interaction: Interaction, key: str, **kwargs: Any):
    if not isinstance(interaction.command, Command):
        raise ValueError(
            "Attempted to translate group text when interaction.command is not a Command"
        )

    if interaction.command.parent is None:
        raise ValueError(
            "Attempted to translate group text when interaction.command.parent is None"
        )

    msg_id = group_text_id(interaction.command.parent, key)
    return await _translate_or_warn(interaction, msg_id, **kwargs)


async def _translate_or_warn(interaction: Interaction, msg_id: str, **kwargs: Any):
    result = await interaction.translate(locale_str(msg_id, **kwargs))

    if result is None:
        logger.warning(f"Failed to translate string: {msg_id}")
        return msg_id

    return result


def command_id(command: TranslationCommand):
    command_name = _format_identifier(command.qualified_name)
    return f"command_{command_name}"


def command_description_id(command: TranslationCommand):
    return f"{command_id(command)}.description"


def command_text_id(command: TranslationCommand, key: str):
    return f"{command_id(command)}.text_{key}"


def group_id(group: Group):
    group_name = _format_identifier(group.qualified_name)
    return f"group_{group_name}"


def group_description_id(group: Group):
    return f"{group_id(group)}.description"


def group_text_id(group: Group, key: str):
    return f"{group_id(group)}.text_{key}"


def parameter_id(parameter: Parameter):
    parameter_name = _format_identifier(parameter.name)
    return f"{command_id(parameter.command)}.parameter_{parameter_name}"


def parameter_description_id(parameter: Parameter):
    return f"{parameter_id(parameter)}_description"


def _format_identifier(identifier: str):
    return _SEPARATOR_PATTERN.sub("-", identifier).replace("/", "")


# https://github.com/projectfluent/python-fluent/issues/209
def format_value_with_attributes(
    l10n: FluentLocalization,
    msg_id: str,
    args: dict[str, Any] | None = None,
) -> str:
    base_msg_id, *parts = msg_id.split(".", 1)
    attribute = parts[0] if parts else None

    for bundle in l10n._bundles():  # pyright: ignore[reportPrivateUsage]
        if not bundle.has_message(base_msg_id):
            continue

        msg = bundle.get_message(base_msg_id)
        value = msg.attributes.get(attribute) if attribute else msg.value
        if not value:
            continue

        val, _errors = bundle.format_pattern(value, args)
        assert not isinstance(val, FluentNone)
        return val

    return msg_id
