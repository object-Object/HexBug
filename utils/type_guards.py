from typing import Any, Mapping, Type, TypedDict, TypeGuard, TypeVar, get_args

T = TypeVar("T", bound=TypedDict)


def is_typeddict_subtype(typeddict: Mapping[str, Any], class_or_type: Type[T], key="type") -> TypeGuard[T]:
    try:
        # this feels really really really gross. but it works
        orig_bases = class_or_type.__orig_bases__  # type: ignore
        return typeddict[key] == get_args(get_args(orig_bases[0])[0])[0]
    except IndexError:
        return False
