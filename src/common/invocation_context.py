"""Context local to one skill invocation."""

from contextlib import contextmanager
from contextvars import ContextVar
from typing import TYPE_CHECKING, Iterator

if TYPE_CHECKING:
    from .harness import Harness

_current_skill_name: ContextVar[str | None] = ContextVar(
    "current_skill_name", default=None
)
_current_harness: ContextVar["Harness | None"] = ContextVar(
    "current_harness", default=None
)


def get_current_skill_name() -> str | None:
    return _current_skill_name.get()


def get_current_harness() -> "Harness | None":
    return _current_harness.get()


@contextmanager
def skill_invocation_context(skill_name: str) -> Iterator[None]:
    token = _current_skill_name.set(skill_name)
    try:
        yield
    finally:
        _current_skill_name.reset(token)


@contextmanager
def harness_invocation_context(harness: "Harness") -> Iterator[None]:
    token = _current_harness.set(harness)
    try:
        yield
    finally:
        _current_harness.reset(token)
