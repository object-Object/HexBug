from abc import ABC, abstractmethod
from typing import Iterator, TypedDict, cast, override

import pfzy
from discord import Interaction
from discord.app_commands import (
    Transform,
    Transformer,
)
from discord.app_commands.models import Choice

from HexBug.core.bot import HexBugBot
from HexBug.data.patterns import PatternInfo


class AutocompleteWord(TypedDict):
    search_term: str
    result: str


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
        for match in matches[:25]:
            word = match["result"]
            if word in seen:
                continue
            seen.add(word)
            yield Choice(name=word, value=word)


class PatternInfoTransformer(PfzyAutocompleteTransformer):
    @override
    async def transform(self, interaction: Interaction, value: str) -> PatternInfo:
        registry = HexBugBot.registry_of(interaction)
        pattern = registry.lookups.name.get(value)
        if pattern is None:
            raise ValueError("Unknown pattern.")
        return pattern

    @override
    def _setup_autocomplete(self, interaction: Interaction):
        self._words.clear()

        registry = HexBugBot.registry_of(interaction)
        for pattern in registry.patterns.values():
            self._words += [
                AutocompleteWord(search_term=pattern.name, result=pattern.name),
                AutocompleteWord(search_term=str(pattern.id), result=pattern.name),
            ]

        self._words.sort(key=lambda w: w["result"].lower())


PatternInfoOption = Transform[PatternInfo, PatternInfoTransformer]
