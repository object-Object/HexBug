from __future__ import annotations

import logging
import re
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Literal

from discord import AppCommandOptionType, Interaction
from discord.app_commands import (
    Choice,
    Command,
    ContextMenu,
    Group,
    Parameter,
    Transformer,
    locale_str,
)

from .commands import AnyCommand

logger = logging.getLogger(__name__)


type TranslationCommand = AnyCommand | ContextMenu

type TranslationValue = str | int | float | datetime


class LocaleEnumTransformer[T: Enum](Transformer):
    _enum_type: type[T]
    _choices: list[Choice[str]]

    def __init__(
        self,
        enum_type: type[T],
        *,
        name: Literal["name", "value"] | Callable[[T], str] = "name",
    ):
        super().__init__()

        self._enum_type = enum_type
        self._choices = []

        for enum in enum_type:
            match name:
                case "name":
                    enum_name = enum.name
                case "value":
                    enum_name = str(enum.value)
                case _:
                    enum_name = name(enum)
            self._choices.append(
                Choice(
                    name=locale_str(enum_name, id=enum_choice_name_id(enum)),
                    value=enum.name,
                )
            )

        if len(self._choices) < 2:
            raise TypeError("enum.Enum requires at least two values.")

    @property
    def _error_display_name(self) -> str:
        return self._enum_type.__name__

    @property
    def type(self) -> AppCommandOptionType:
        return AppCommandOptionType.string

    @property
    def choices(self) -> list[Choice[Any]]:
        return self._choices

    async def transform(self, interaction: Interaction, value: Any) -> T:
        return self._enum_type[value]


async def translate(
    interaction: Interaction,
    key: str,
    **kwargs: TranslationValue,
):
    return await _translate_or_warn(interaction, key, **kwargs)


async def translate_command_text(
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


async def translate_choice_text(
    interaction: Interaction,
    enum: Enum,
    key: str,
    **kwargs: TranslationValue,
):
    msg_id = enum_choice_text_id(enum, key)
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


def enum_choice_name_id(enum: Enum):
    class_ = enum.__class__
    return choice_name_id(f"{class_.__module__}.{class_.__qualname__}", enum.name)


def enum_choice_text_id(enum: Enum, key: str):
    return f"{enum_choice_name_id(enum)}_text_{key}"


def choice_name_id(type_name: str, item_name: str):
    type_name = _format_identifier(type_name)
    item_name = _format_identifier(item_name)
    return f"choice_{type_name}.{item_name}"


_SEPARATOR_PATTERN = re.compile(r"[. _-]+")


def _format_identifier(identifier: str):
    return _SEPARATOR_PATTERN.sub("-", identifier).replace("/", "")
