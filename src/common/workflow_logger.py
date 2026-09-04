"""Workflow-agnostic structured logging contexts."""

import logging
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Iterator

_route: ContextVar[tuple[str, str] | None] = ContextVar("workflow_route", default=None)


class _RouteAdapter(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        domain, task_list = _route.get() or ("", "")
        kwargs.setdefault("extra", {}).update(
            {"domain": domain, "task_list": task_list}
        )
        return msg, kwargs


@contextmanager
def worker_log_context(
    *, domain: str, task_list: str
) -> Iterator[logging.LoggerAdapter]:
    """Attach a workflow module route to worker records."""
    token = _route.set((domain, task_list))
    try:
        yield _RouteAdapter(logging.getLogger("workflow.worker"), {})
    finally:
        _route.reset(token)


def get_worker_logger() -> logging.LoggerAdapter:
    return _RouteAdapter(logging.getLogger("workflow.worker"), {})


@contextmanager
def workflow_log_context(*args, **kwargs) -> Iterator[logging.Logger]:
    yield logging.getLogger("workflow.execution")


@contextmanager
def client_log_context(*args, **kwargs) -> Iterator[logging.Logger]:
    yield logging.getLogger("workflow.client")


def get_workflow_logger() -> logging.Logger:
    return logging.getLogger("workflow.execution")


def get_client_logger() -> logging.Logger:
    return logging.getLogger("workflow.client")


def get_activity_logger() -> logging.Logger:
    return logging.getLogger("workflow.activity")


def get_workflow_log_path() -> None:
    return None
