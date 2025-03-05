from abc import ABC, abstractmethod
from typing import Any, Iterator, override

import pfzy
from discord import Interaction
from discord.app_commands import (
    Transform,
    Transformer,
)
from discord.app_commands.models import Choice

from HexBug.core.bot import HexBugBot
from HexBug.data.patterns import PatternInfo


class PfzyAutocompleteTransformer(Transformer, ABC):
    # FIXME: this is probably not how this should work.
    def __init_subclass__(cls):
        cls._words: list[str] = []
        cls._synonyms: dict[str, str] = {}

    @abstractmethod
    def _setup_autocomplete(self, interaction: Interaction):
        """Adds values to self._words and self._synonyms."""

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
            self._words,  # type: ignore
            scorer=pfzy.fzy_scorer,
            key="value",
        )

        return [
            Choice(name=word, value=word) for word in self._process_matches(matches)
        ]

    def _preprocess_input(self, text: str) -> str:
        return text.lower().strip()

    def _process_matches(self, matches: list[dict[str, Any]]) -> Iterator[str]:
        seen = set[str]()
        for match in matches[:25]:
            word: str = match["value"]
            if word in self._synonyms:
                word = self._synonyms[word]
            if word in seen:
                continue
            seen.add(word)
            yield word


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
        self._synonyms.clear()

        registry = HexBugBot.registry_of(interaction)
        for pattern in registry.patterns.values():
            self._words += [
                pattern.name,
                str(pattern.id),
            ]
            self._synonyms[str(pattern.id)] = pattern.name

        self._words.sort(key=str.lower)


PatternInfoOption = Transform[PatternInfo, PatternInfoTransformer]
