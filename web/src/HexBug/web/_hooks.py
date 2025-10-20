from importlib.resources import Package
from pathlib import Path
from typing import Any

from hexdoc.core import Properties
from hexdoc.plugin import (
    HookReturn,
    ModPlugin,
    ModPluginImpl,
    ModPluginWithBook,
    UpdateTemplateArgsImpl,
    hookimpl,
)
from markupsafe import Markup
from typing_extensions import override

import HexBug.web
from HexBug.__version__ import VERSION
from HexBug.data.registry import HexBugRegistry
from HexBug.data.utils.hexdoc import monkeypatch_hexdoc_hexcasting


class BookOfHexxyPlugin(ModPluginImpl, UpdateTemplateArgsImpl):
    @staticmethod
    @hookimpl(tryfirst=True)
    def hexdoc_mod_plugin(branch: str) -> ModPlugin:
        # this SHOULD run early enough...
        monkeypatch_hexdoc_hexcasting()

        return BookOfHexxyModPlugin(branch=branch)

    @staticmethod
    @hookimpl
    def hexdoc_update_template_args(template_args: dict[str, Any]) -> None:
        props = Properties.of(template_args)

        path = Path(props.extra["bookofhexxy"]["registry_path"])
        registry_json = path.read_text("utf-8")
        registry = HexBugRegistry.model_validate_json(registry_json)

        template_args |= {
            "bookofhexxy_registry_json": Markup(registry_json),
            "bookofhexxy_mods": registry.mods,
        }


class BookOfHexxyModPlugin(ModPluginWithBook):
    @property
    @override
    def modid(self) -> str:
        return "bookofhexxy"

    @property
    @override
    def full_version(self) -> str:
        return VERSION

    @property
    @override
    def mod_version(self) -> str:
        return VERSION

    @property
    @override
    def plugin_version(self) -> str:
        return VERSION

    @property
    @override
    def versioned_site_path(self) -> Path:
        return self.site_root / VERSION

    @override
    def resource_dirs(self) -> HookReturn[Package]:
        return []

    @override
    def jinja_template_root(self) -> tuple[Package, str]:
        return HexBug.web, "_templates"
