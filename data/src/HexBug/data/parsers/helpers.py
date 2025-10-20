from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:

    def v_args[T](
        inline: bool = False,
        meta: bool = False,
        tree: bool = False,
    ) -> Callable[[T], T]: ...

else:
    from lark import v_args
