from collections import defaultdict

from discord import app_commands
from discord.ext import commands

from hexdecode.hexast import Registry


def build_autocomplete(
    initial_choices: list[tuple[app_commands.Choice, list[str]]]
) -> dict[str, list[app_commands.Choice]]:
    autocomplete: defaultdict[str, set[app_commands.Choice]] = defaultdict(set)
    for choice, other_names in initial_choices:
        for name in other_names + [choice.name]:
            name = name.lower()
            for i in range(len(name)):
                for j in range(i, len(name)):
                    autocomplete[name[i : j + 1]].add(choice)
        autocomplete[""].add(choice)

    return {key: sorted(list(value), key=lambda c: c.name) for key, value in autocomplete.items()}


class HexBugBot(commands.Bot):
    def __init__(self, registry: Registry, **kwargs) -> None:
        super().__init__(**kwargs)
        self.registry = registry
