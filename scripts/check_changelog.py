import sys

from HexBug.__version__ import VERSION
from HexBug.utils.changelog import parse_changelog

if __name__ == "__main__":
    with open("CHANGELOG.md", "r") as f:
        changelog = f.read()

    versions = {entry.version for entry in parse_changelog(changelog) if entry.date}

    if VERSION not in versions:
        print(f"No changelog entry found for bot version: {VERSION}")
        sys.exit(1)
