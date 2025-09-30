from typing import Any

from hexdoc.core import ResourceLocation
from sqlalchemy import TypeDecorator, types
from sqlalchemy.engine.interfaces import Dialect


class ResourceLocationType(TypeDecorator[ResourceLocation]):
    impl = types.String

    cache_ok = True

    def process_bind_param(self, value: ResourceLocation | None, dialect: Dialect):
        if value is not None:
            return str(value)

    def process_result_value(self, value: Any | None, dialect: Dialect):
        if value is not None:
            return ResourceLocation.from_str(value)
