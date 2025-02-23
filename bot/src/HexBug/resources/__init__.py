from contextlib import contextmanager
from importlib import resources


def get_resource(name: str):
    files = resources.files()
    return files / name


def load_resource(name: str, encoding: str = "utf-8"):
    return get_resource(name).read_text(encoding)


@contextmanager
def load_resource_dir(name: str):
    resource = get_resource(name)
    with resources.as_file(resource) as path:
        yield path
