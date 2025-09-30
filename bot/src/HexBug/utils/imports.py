from importlib import resources
from types import ModuleType


def fullname(cls: type):
    return f"{cls.__module__}.{cls.__qualname__}"


def iter_modules(parent: ModuleType, skip_internal: bool = False):
    with resources.as_file(resources.files(parent)) as parent_path:
        for path in parent_path.rglob("*.py"):
            if path.stem in {"__init__", "__main__"} or (
                skip_internal and path.stem.startswith("_")
            ):
                continue
            path = path.relative_to(parent_path).with_suffix("")
            yield ".".join([parent.__name__, *path.parts])
