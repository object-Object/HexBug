import logging
import re
from datetime import datetime

from discord import Interaction
from discord.app_commands import (
    Command,
    ContextMenu,
    Group,
    Parameter,
    locale_str,
)

from HexBug.utils.discord.commands import AnyCommand

logger = logging.getLogger(__name__)

_SEPARATOR_PATTERN = re.compile(r"[ _-]+")

type TranslationCommand = AnyCommand | ContextMenu

type TranslationValue = str | int | float | datetime


async def translate_text(
    interaction: Interaction,
    key: str,
    **kwargs: TranslationValue,
):
    if interaction.command is None:
        raise ValueError(
            "Attempted to translate command text when interaction.command is None"
        )

    msg_id = command_text_id(interaction.command, key)
    return await _translate_or_warn(interaction, msg_id, **kwargs)


async def translate_group_text(
    interaction: Interaction,
    key: str,
    **kwargs: TranslationValue,
):
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


async def _translate_or_warn(
    interaction: Interaction,
    msg_id: str,
    **kwargs: TranslationValue,
):
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
