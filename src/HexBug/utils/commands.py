from collections import defaultdict

from aiohttp import ClientSession
from discord import Webhook, app_commands
from discord.ext import commands

from ..hexdecode.registry import Registry


def build_autocomplete(
    initial_choices: list[tuple[app_commands.Choice, list[str]]],
) -> dict[str, list[app_commands.Choice]]:
    autocomplete: defaultdict[str, set[app_commands.Choice]] = defaultdict(set)
    for choice, other_names in initial_choices:
        for name in other_names + [choice.name]:
            name = name.lower()
            for i in range(len(name)):
                for j in range(i, len(name)):
                    autocomplete[name[i : j + 1]].add(choice)
        autocomplete[""].add(choice)

    return {
        key: sorted(list(value), key=lambda c: c.name)
        for key, value in autocomplete.items()
    }


class HexBugBot(commands.Bot):
    def __init__(
        self,
        registry: Registry,
        session: ClientSession,
        log_webhook_url: str,
        health_check_channel_id: int,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.registry = registry
        self.session = session
        self.log_webhook = Webhook.from_url(log_webhook_url, session=session)
        self.health_check_channel_id = health_check_channel_id
