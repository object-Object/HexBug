import re
from dataclasses import dataclass, field
from typing import Iterator

from discord import Embed

_VERSION_PATTERN = re.compile(
    r"## (?:`(?P<version>[^`]+)` - (?P<date>\d{4}-\d{2}-\d{2})|(?P<unknown>.+))"
)


@dataclass(kw_only=True)
class ChangelogEntry:
    version: str
    date: str | None
    body: str

    def __post_init__(self):
        self.embed = Embed(
            description=f"## {self.version}\n{self.body}",
        ).set_footer(
            text=self.date,
        )


@dataclass(kw_only=True)
class ChangelogEntryBuilder:
    version: str
    date: str | None = None
    body: list[str] = field(default_factory=lambda: [])

    def build(self):
        return ChangelogEntry(
            version=self.version,
            date=self.date,
            body="\n".join(self.body),
        )


def parse_changelog(changelog: str) -> Iterator[ChangelogEntry]:
    builder = None

    for line in changelog.splitlines():
        line = line.rstrip()

        if match := _VERSION_PATTERN.match(line):
            if builder:
                yield builder.build()

            if version := match["version"]:
                builder = ChangelogEntryBuilder(version=version, date=match["date"])
            else:
                builder = ChangelogEntryBuilder(version=match["unknown"])

        elif builder and line:
            builder.body.append(line)

    if builder:
        yield builder.build()
