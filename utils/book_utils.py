from typing import Mapping, Type, TypeGuard, TypeVar, get_args

from utils.book_types import BookPage

U = TypeVar("U", bound=BookPage)


def isbookpage(page: Mapping, book_type: Type[U]) -> TypeGuard[U]:
    try:
        # this feels really really really gross. but it works
        orig_bases = book_type.__orig_bases__  # type: ignore
        return page["type"] == get_args(get_args(orig_bases[0])[0])[0]
    except IndexError:
        return False
