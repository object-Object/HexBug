from contextlib import contextmanager
from contextvars import ContextVar


@contextmanager
def set_contextvar[T](var: ContextVar[T], value: T):
    token = var.set(value)
    try:
        yield
    finally:
        var.reset(token)
