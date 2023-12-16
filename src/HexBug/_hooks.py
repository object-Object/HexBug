from importlib.resources import Package

from hexdoc.plugin import (
    HookReturn,
    ModPlugin,
    ModPluginImpl,
    ModPluginWithBook,
    hookimpl,
)
from typing_extensions import override


class HexBugPlugin(ModPluginImpl):
    @staticmethod
    @hookimpl
    def hexdoc_mod_plugin(branch: str) -> ModPlugin:
        return HexBugModPlugin(branch=branch)


class HexBugModPlugin(ModPluginWithBook):
    @property
    @override
    def modid(self) -> str:
        return "hexbug"

    @property
    @override
    def full_version(self) -> str:
        return ""

    @property
    @override
    def mod_version(self) -> str:
        return ""

    @property
    @override
    def plugin_version(self) -> str:
        return ""

    @override
    def resource_dirs(self) -> HookReturn[Package]:
        return []
