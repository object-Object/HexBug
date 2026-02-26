import shutil
from importlib.resources import Package
from pathlib import Path

from hexdoc.cli.app import LoadedBookInfo
from hexdoc.core import Properties
from hexdoc.plugin import (
    HookReturn,
    ModPlugin,
    ModPluginImpl,
    ModPluginWithBook,
    UpdateTemplateArgsImpl,
    hookimpl,
)
from jinja2.sandbox import SandboxedEnvironment
from typing_extensions import override

import HexBug.web
from HexBug.__version__ import VERSION
from HexBug.data.registry import HexBugRegistry
from HexBug.data.utils.hexdoc import monkeypatch_hexdoc, monkeypatch_hexdoc_hexcasting


class BookOfHexxyPlugin(ModPluginImpl, UpdateTemplateArgsImpl):
    @staticmethod
    @hookimpl(tryfirst=True)
    def hexdoc_mod_plugin(branch: str) -> ModPlugin:
        # this SHOULD run early enough...
        monkeypatch_hexdoc()
        monkeypatch_hexdoc_hexcasting()

        return BookOfHexxyModPlugin(branch=branch)


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

    @override
    def pre_render_site(
        self,
        props: Properties,
        books: list[LoadedBookInfo],
        env: SandboxedEnvironment,
        output_dir: Path,
    ) -> None:
        registry_path = Path(props.extra["bookofhexxy"]["registry_path"])

        shutil.copyfile(registry_path, output_dir / "registry.json")

        registry = HexBugRegistry.load(registry_path)
        for book in books:
            book.context["bookofhexxy_mods"] = registry.mods
