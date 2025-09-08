from abc import ABC, abstractmethod
from typing import Any, Iterator, TypedDict, cast, override

import pfzy
import sqlalchemy as sa
from discord import Interaction
from discord.app_commands import (
    Transform,
    Transformer,
)
from discord.app_commands.models import Choice
from discord.app_commands.transformers import EnumNameTransformer, EnumValueTransformer
from hexdoc.core import ResourceLocation

from HexBug.core.bot import HexBugBot
from HexBug.data.hex_math import VALID_SIGNATURE_PATTERN, HexDir
from HexBug.data.mods import ModInfo, Modloader
from HexBug.data.patterns import PatternInfo
from HexBug.data.special_handlers import SpecialHandlerInfo
from HexBug.db.models import PerWorldPattern


class AutocompleteWord(TypedDict):
    search_term: str
    name: str
    value: str


class AutocompleteResult(AutocompleteWord):
    indices: list[int]


class PfzyAutocompleteTransformer(Transformer, ABC):
    def __init_subclass__(cls):
        cls._words: list[AutocompleteWord] = []

    @abstractmethod
    async def _setup_autocomplete(self, interaction: Interaction) -> None:
        """Adds values to self._words."""

    async def _get_words(self, interaction: Interaction) -> list[AutocompleteWord]:
        if not self._words:
            await self._setup_autocomplete(interaction)
        return self._words

    @override
    async def autocomplete(  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        interaction: Interaction,
        value: str,
    ) -> list[Choice[str]]:
        matches = await pfzy.fuzzy_match(
            value,
            await self._get_words(interaction),  # pyright: ignore[reportArgumentType]
            scorer=pfzy.fzy_scorer,
            key="search_term",
        )

        return list(self._process_matches(cast(list[AutocompleteResult], matches)))

    def _preprocess_input(self, text: str) -> str:
        return text.lower().strip()

    def _process_matches(
        self,
        matches: list[AutocompleteResult],
    ) -> Iterator[Choice[str]]:
        seen = set[str]()
        for match in matches:
            if match["name"] in seen:
                continue
            seen.add(match["name"])
            yield Choice(name=match["name"], value=match["value"])
            if len(seen) >= 25:
                break


class ModAuthorTransformer(PfzyAutocompleteTransformer):
    _authors: dict[str, str] = {}

    @override
    async def transform(self, interaction: Interaction, value: str) -> str:
        author = self._authors.get(value.lower().strip())
        if author is None:
            raise ValueError("Unknown author.")
        return author

    @override
    async def _setup_autocomplete(self, interaction: Interaction):
        self._words.clear()
        self._authors.clear()

        registry = HexBugBot.registry_of(interaction)
        for mod in registry.mods.values():
            author = mod.github_author
            self._words.append(
                AutocompleteWord(
                    search_term=author,
                    name=author,
                    value=author,
                )
            )
            self._authors[author.lower().strip()] = author

        self._words.sort(key=lambda w: w["name"].lower())


class ModInfoTransformer(PfzyAutocompleteTransformer):
    @override
    async def transform(self, interaction: Interaction, value: str) -> ModInfo:
        registry = HexBugBot.registry_of(interaction)
        mod = registry.mods.get(value)
        if mod is None:
            raise ValueError("Unknown mod.")
        return mod

    @override
    async def _setup_autocomplete(self, interaction: Interaction):
        self._words.clear()

        registry = HexBugBot.registry_of(interaction)
        for mod in registry.mods.values():
            for search_term in [
                mod.name,
                mod.id,
                f"{mod.github_author}/{mod.github_repo}",
            ]:
                self._words.append(
                    AutocompleteWord(
                        search_term=search_term,
                        name=mod.name,
                        value=mod.id,
                    )
                )


class PatternInfoTransformer(PfzyAutocompleteTransformer):
    @override
    async def transform(self, interaction: Interaction, value: str) -> PatternInfo:
        pattern_id = ResourceLocation.from_str(value)
        registry = HexBugBot.registry_of(interaction)
        pattern = registry.patterns.get(pattern_id)
        if pattern is None:
            raise ValueError("Unknown pattern.")
        return pattern

    @override
    async def _setup_autocomplete(self, interaction: Interaction):
        self._words.clear()

        registry = HexBugBot.registry_of(interaction)
        for pattern in registry.patterns.values():
            if pattern.is_hidden:
                continue
            for search_term in [
                pattern.name,
                str(pattern.id),
            ]:
                self._words.append(
                    AutocompleteWord(
                        search_term=search_term,
                        name=pattern.name,
                        value=str(pattern.id),
                    )
                )

        self._words.sort(key=lambda w: w["name"].lower())


class SpecialHandlerInfoTransformer(PfzyAutocompleteTransformer):
    @override
    async def transform(
        self,
        interaction: Interaction,
        value: str,
    ) -> SpecialHandlerInfo:
        handler_id = ResourceLocation.from_str(value)
        registry = HexBugBot.registry_of(interaction)
        info = registry.special_handlers.get(handler_id)
        if info is None:
            raise ValueError("Unknown special handler.")
        return info

    @override
    async def _setup_autocomplete(self, interaction: Interaction):
        self._words.clear()

        registry = HexBugBot.registry_of(interaction)
        for info in registry.special_handlers.values():
            for search_term in [
                info.base_name,
                str(info.id),
            ]:
                self._words.append(
                    AutocompleteWord(
                        search_term=search_term,
                        name=info.base_name,
                        value=str(info.id),
                    )
                )

        self._words.sort(key=lambda w: w["name"].lower())


class PerWorldPatternTransformer(PfzyAutocompleteTransformer):
    def __init__(self, autocomplete_filter_user: bool = False):
        super().__init__()
        self.autocomplete_filter_user = autocomplete_filter_user

    @override
    async def transform(
        self,
        interaction: Interaction,
        value: str,
    ) -> PerWorldPattern:
        assert interaction.guild_id
        id_ = ResourceLocation.from_str(value)
        bot = HexBugBot.of(interaction)

        async with bot.db_session() as session:
            stmt = (
                sa.select(PerWorldPattern)
                .where(PerWorldPattern.id == id_)
                .where(PerWorldPattern.guild_id == interaction.guild_id)
            )

            result = await session.scalar(stmt)
            if result is None:
                raise ValueError(
                    "Pattern has not been added to this server's database."
                    if id_ in bot.registry.patterns
                    else "Pattern not found."
                )
            return result

    @override
    async def _get_words(self, interaction: Interaction) -> list[AutocompleteWord]:
        if not interaction.guild_id:
            return []

        bot = HexBugBot.of(interaction)

        # TODO: this feels inefficient
        words = list[AutocompleteWord]()
        async with bot.db_session() as session:
            stmt = sa.select(PerWorldPattern).where(
                PerWorldPattern.guild_id == interaction.guild_id
            )
            if self.autocomplete_filter_user:
                stmt = stmt.where(PerWorldPattern.user_id == interaction.user.id)

            for entry in await session.scalars(stmt):
                if info := bot.registry.patterns.get(entry.id):
                    if info.is_hidden:
                        continue
                    for search_term in [
                        info.name,
                        str(info.id),
                    ]:
                        words.append(
                            AutocompleteWord(
                                search_term=search_term,
                                name=info.name,
                                value=str(entry.id),
                            )
                        )
                else:
                    words.append(
                        AutocompleteWord(
                            search_term=str(entry.id),
                            name=str(entry.id),
                            value=str(entry.id),
                        )
                    )
        return words

    @override
    async def _setup_autocomplete(self, interaction: Interaction) -> None:
        raise NotImplementedError()


class PatternSignatureTransformer(Transformer):
    async def transform(self, interaction: Interaction, value: Any) -> Any:
        signature = value.lower()
        if signature in ["-", '"-"']:
            signature = ""
        elif not VALID_SIGNATURE_PATTERN.fullmatch(signature):
            raise ValueError(
                "Invalid signature, must only contain the characters `aqweds`."
            )
        return signature


class BetterEnumValueTransformer(EnumValueTransformer):
    def __init__(self, enum: Any) -> None:
        super().__init__(enum)
        for choice in self._choices:
            choice.name = choice.value


ModAuthorOption = Transform[str, ModAuthorTransformer]

ModInfoOption = Transform[ModInfo, ModInfoTransformer]

PatternInfoOption = Transform[PatternInfo, PatternInfoTransformer]

SpecialHandlerInfoOption = Transform[SpecialHandlerInfo, SpecialHandlerInfoTransformer]

PerWorldPatternOption = Transform[PerWorldPattern, PerWorldPatternTransformer]

PatternSignatureOption = Transform[str, PatternSignatureTransformer]

ModloaderOption = Transform[Modloader, BetterEnumValueTransformer(Modloader)]

HexDirOption = Transform[HexDir, EnumNameTransformer(HexDir)]
