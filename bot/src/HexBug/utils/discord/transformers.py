from abc import ABC, abstractmethod
from typing import Iterator, TypedDict, cast, override

import pfzy
from discord import Interaction
from discord.app_commands import (
    Transform,
    Transformer,
)
from discord.app_commands.models import Choice
from hexdoc.core import ResourceLocation

from HexBug.core.bot import HexBugBot
from HexBug.data.mods import ModInfo
from HexBug.data.patterns import PatternInfo
from HexBug.data.special_handlers import SpecialHandlerInfo


class AutocompleteWord(TypedDict):
    search_term: str
    name: str
    value: str


class AutocompleteResult(AutocompleteWord):
    indices: list[int]


class PfzyAutocompleteTransformer(Transformer, ABC):
    # FIXME: this is probably not how this should work.
    def __init_subclass__(cls):
        cls._words: list[AutocompleteWord] = []

    @abstractmethod
    def _setup_autocomplete(self, interaction: Interaction):
        """Adds values to self._words."""

    @override
    async def autocomplete(  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        interaction: Interaction,
        value: str,
    ) -> list[Choice[str]]:
        if not self._words:
            self._setup_autocomplete(interaction)

        matches = await pfzy.fuzzy_match(
            value,
            self._words,  # pyright: ignore[reportArgumentType]
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
    def _setup_autocomplete(self, interaction: Interaction):
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
    def _setup_autocomplete(self, interaction: Interaction):
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
    def _setup_autocomplete(self, interaction: Interaction):
        self._words.clear()

        registry = HexBugBot.registry_of(interaction)
        for pattern in registry.patterns.values():
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
    def _setup_autocomplete(self, interaction: Interaction):
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


ModAuthorOption = Transform[str, ModAuthorTransformer]

ModInfoOption = Transform[ModInfo, ModInfoTransformer]

PatternInfoOption = Transform[PatternInfo, PatternInfoTransformer]

SpecialHandlerInfoOption = Transform[SpecialHandlerInfo, SpecialHandlerInfoTransformer]
