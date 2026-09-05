from contextlib import contextmanager
from contextvars import ContextVar
from typing import Iterator

_current_skill_name: ContextVar[str | None] = ContextVar(
    "current_skill_name", default=None
)


def get_current_skill_name() -> str | None:
    return _current_skill_name.get()


@contextmanager
def skill_invocation_context(skill_name: str) -> Iterator[None]:
    token = _current_skill_name.set(skill_name)
    try:
        yield
    finally:
        _current_skill_name.reset(token)
