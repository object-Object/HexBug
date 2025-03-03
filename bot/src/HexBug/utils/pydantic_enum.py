from enum import Enum
from typing import Any

from pydantic import GetCoreSchemaHandler
from pydantic_core import core_schema


def pydantic_enum[E: Enum](enum_cls: type[E]) -> type[E]:
    """Decorator that makes Pydantic (de)serialize an enum by name instead of by value.

    https://github.com/pydantic/pydantic/discussions/2980#discussioncomment-9912210
    """

    def __get_pydantic_core_schema__(
        cls: type[E], source_type: Any, handler: GetCoreSchemaHandler
    ):
        assert source_type is cls

        def get_enum(
            value: Any, validate_next: core_schema.ValidatorFunctionWrapHandler
        ):
            if isinstance(value, cls):
                return value
            else:
                name: str = validate_next(value)
                return enum_cls[name]

        def serialize(enum: E):
            return enum.name

        expected = [member.name for member in cls]
        name_schema = core_schema.literal_schema(expected)

        return core_schema.no_info_wrap_validator_function(
            get_enum,
            name_schema,
            ref=cls.__name__,
            serialization=core_schema.plain_serializer_function_ser_schema(serialize),
        )

    setattr(
        enum_cls,
        "__get_pydantic_core_schema__",
        classmethod(__get_pydantic_core_schema__),
    )
    return enum_cls
