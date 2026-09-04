"""Workflow-agnostic structured logging contexts."""

import json
import logging
import os
import re
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator

try:
    from cadence import activity
except ImportError:
    activity = None

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent / "workflow_logging.config.json"
DEFAULT_LOG_ROOT = REPO_ROOT / ".process" / "logs"
DEFAULT_LEVELS = {
    "worker": "INFO",
    "workflow": "INFO",
    "client": "INFO",
    "activity": "DEBUG",
    "devin": "DEBUG",
}
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
_SAFE_COMPONENT_RE = re.compile(r"[^A-Za-z0-9_-]+")
_route: ContextVar[tuple[str, str] | None] = ContextVar("workflow_route", default=None)


@dataclass(frozen=True)
class WorkflowLoggerConfig:
    log_root: Path = DEFAULT_LOG_ROOT
    worker_level: str = DEFAULT_LEVELS["worker"]
    workflow_level: str = DEFAULT_LEVELS["workflow"]
    client_level: str = DEFAULT_LEVELS["client"]
    activity_level: str = DEFAULT_LEVELS["activity"]
    devin_level: str = DEFAULT_LEVELS["devin"]

    @classmethod
    def load(cls, config_path: Path = DEFAULT_CONFIG_PATH) -> "WorkflowLoggerConfig":
        data = json.loads(config_path.read_text()) if config_path.exists() else {}
        levels = data.get("levels", {})
        log_root = Path(
            os.environ.get(
                "STORY_ANALYSIS_LOG_ROOT",
                data.get("log_root", str(DEFAULT_LOG_ROOT)),
            )
        )
        if not log_root.is_absolute():
            log_root = REPO_ROOT / log_root
        return cls(
            log_root=log_root,
            worker_level=levels.get("worker", DEFAULT_LEVELS["worker"]),
            workflow_level=levels.get("workflow", DEFAULT_LEVELS["workflow"]),
            client_level=levels.get("client", DEFAULT_LEVELS["client"]),
            activity_level=levels.get("activity", DEFAULT_LEVELS["activity"]),
            devin_level=levels.get("devin", DEFAULT_LEVELS["devin"]),
        )


@dataclass
class _LogBundle:
    activity: logging.Logger
    devin: logging.Logger
    artifact_dir: Path | None = None


_CURRENT_BUNDLE: ContextVar[_LogBundle | None] = ContextVar(
    "workflow_log_bundle", default=None
)


class _RouteAdapter(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        domain, task_list = _route.get() or ("", "")
        kwargs.setdefault("extra", {}).update(
            {"domain": domain, "task_list": task_list}
        )
        return msg, kwargs


def _sanitize_component(value: str) -> str:
    sanitized = _SAFE_COMPONENT_RE.sub("_", value).strip("_")
    return sanitized or "unknown"


def _parse_level(value: Any) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        parsed = logging.getLevelName(value.upper())
        if isinstance(parsed, int):
            return parsed
    return logging.INFO


def _create_file_logger(name: str, path: Path, level: int) -> logging.Logger:
    path.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger(f"{name}.{re.sub(r'[^A-Za-z0-9_]+', '_', str(path)).strip('_')}")
    logger.setLevel(level)
    logger.handlers = []
    handler = logging.FileHandler(path)
    handler.setLevel(level)
    handler.setFormatter(logging.Formatter(LOG_FORMAT))
    logger.addHandler(handler)
    logger.propagate = False
    return logger


def _close_logger(logger: logging.Logger) -> None:
    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        handler.close()


def _resolve_activity_info(activity_info: Any = None) -> Any:
    if activity_info is not None:
        return activity_info
    if activity is not None and activity.in_activity():
        return activity.info()
    return None


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
def activity_log_context(
    activity_info: Any = None,
    config: WorkflowLoggerConfig | None = None,
) -> Iterator[_LogBundle]:
    info = _resolve_activity_info(activity_info)
    if info is None:
        bundle = _LogBundle(
            activity=logging.getLogger("workflow.activity"),
            devin=logging.getLogger("workflow.devin"),
        )
        token = _CURRENT_BUNDLE.set(bundle)
        try:
            yield bundle
        finally:
            _CURRENT_BUNDLE.reset(token)
        return

    cfg = config or WorkflowLoggerConfig.load()
    artifact_dir = (
        cfg.log_root
        / _sanitize_component(getattr(info, "workflow_id", ""))
        / _sanitize_component(getattr(info, "workflow_run_id", ""))
        / "activities"
        / (
            f"{_sanitize_component(getattr(info, 'activity_type', 'activity'))}_"
            f"{_sanitize_component(getattr(info, 'activity_id', ''))}_"
            f"{getattr(info, 'attempt', 0)}"
        )
    )
    activity_logger = _create_file_logger(
        "workflow.activity", artifact_dir / "activity.log", _parse_level(cfg.activity_level)
    )
    devin_logger = _create_file_logger(
        "workflow.devin", artifact_dir / "devin.log", _parse_level(cfg.devin_level)
    )
    bundle = _LogBundle(activity_logger, devin_logger, artifact_dir)
    token = _CURRENT_BUNDLE.set(bundle)
    try:
        yield bundle
    finally:
        _CURRENT_BUNDLE.reset(token)
        _close_logger(activity_logger)
        _close_logger(devin_logger)


def get_activity_artifact_dir() -> Path | None:
    bundle = _CURRENT_BUNDLE.get()
    return bundle.artifact_dir if bundle is not None else None


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
    bundle = _CURRENT_BUNDLE.get()
    return bundle.activity if bundle is not None else logging.getLogger("workflow.activity")


def get_devin_logger() -> logging.Logger:
    bundle = _CURRENT_BUNDLE.get()
    return bundle.devin if bundle is not None else logging.getLogger("workflow.devin")


def get_workflow_log_path() -> None:
    return None
