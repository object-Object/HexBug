import logging
from contextlib import ExitStack
from typing import Any

from discord import Locale
from discord.app_commands import (
    TranslationContextLocation,
    TranslationContextTypes,
    Translator,
    locale_str,
)
from fluent.runtime import FluentLocalization, FluentResourceLoader
from fluent.runtime.types import FluentNone

from HexBug.resources import load_resource_dir
from HexBug.utils.discord.translation import (
    command_description_id,
    command_id,
    group_description_id,
    group_id,
    parameter_description_id,
    parameter_id,
)

logger = logging.getLogger(__name__)


class HexBugTranslator(Translator):
    async def load(self) -> None:
        self.exit_stack = ExitStack()

        path = self.exit_stack.enter_context(load_resource_dir("lang"))
        loader = FluentResourceLoader(path.as_posix() + "/{locale}")

        self.default_l10n = FluentLocalization(
            locales=["en-US"],
            resource_ids=["main.ftl"],
            resource_loader=loader,
        )

        self.l10n = dict[Locale, FluentLocalization]()
        for locale_dir in path.iterdir():
            if locale_dir.is_dir():
                locale = Locale(locale_dir.name)
                self.l10n[locale] = FluentLocalization(
                    locales=[locale.value, "en-US"],
                    resource_ids=["main.ftl"],
                    resource_loader=loader,
                )

    async def unload(self) -> None:
        self.exit_stack.close()

    async def translate(
        self,
        string: locale_str,
        locale: Locale,
        context: TranslationContextTypes,
        *,
        fallback: bool = True,
    ) -> str | None:
        msg_id = self.get_msg_id(string, context)
        result = format_value_with_attributes(
            self.l10n.get(locale, self.default_l10n),
            msg_id,
            string.extras,
            fallback,
        )
        if result == msg_id:
            return string.message
        return result

    def get_msg_id(self, string: locale_str, context: TranslationContextTypes) -> str:
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


# https://github.com/projectfluent/python-fluent/issues/209
def format_value_with_attributes(
    l10n: FluentLocalization,
    msg_id: str,
    args: dict[str, Any] | None = None,
    fallback: bool = True,
) -> str:
    base_msg_id, *parts = msg_id.split(".", 1)
    attribute = parts[0] if parts else None

    for bundle in l10n._bundles():  # pyright: ignore[reportPrivateUsage]
        if not bundle.has_message(base_msg_id):
            if fallback:
                continue
            break

        msg = bundle.get_message(base_msg_id)
        value = msg.attributes.get(attribute) if attribute else msg.value
        if not value:
            if fallback:
                continue
            break

        val, _errors = bundle.format_pattern(value, args)
        assert not isinstance(val, FluentNone)
        return val

    return msg_id
