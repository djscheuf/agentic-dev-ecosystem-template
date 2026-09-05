"""Workflow-agnostic structured logging contexts."""

import json
import logging
import os
import re
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator, Optional

try:
    from cadence import activity
except ImportError:
    activity = None

try:
    from cadence.workflow import WorkflowContext
except ImportError:
    WorkflowContext = None

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
    workflow: logging.Logger
    client: logging.Logger
    artifact_dir: Optional[Path] = None
    activity_path: Optional[Path] = None
    devin_path: Optional[Path] = None
    workflow_path: Optional[Path] = None
    client_path: Optional[Path] = None


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


def _resolve_workflow_info(workflow_info: Any = None) -> Any:
    if workflow_info is not None:
        return workflow_info
    if WorkflowContext is not None and WorkflowContext.is_set():
        return WorkflowContext.get().info()
    return None


def _relative_or_absolute(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


@contextmanager
def worker_log_context(
    *, domain: str, task_list: str
) -> Iterator[logging.LoggerAdapter]:
    token = _route.set((domain, task_list))
    try:
        yield _RouteAdapter(logging.getLogger("workflow.worker"), {})
    finally:
        _route.reset(token)


def get_worker_logger() -> logging.LoggerAdapter:
    return _RouteAdapter(logging.getLogger("workflow.worker"), {})


def _fallback_bundle() -> _LogBundle:
    return _LogBundle(
        activity=logging.getLogger("workflow.activity"),
        devin=logging.getLogger("workflow.devin"),
        workflow=logging.getLogger("workflow.execution"),
        client=logging.getLogger("workflow.client"),
    )


@contextmanager
def activity_log_context(
    activity_info: Any = None,
    config: WorkflowLoggerConfig | None = None,
) -> Iterator[_LogBundle]:
    info = _resolve_activity_info(activity_info)
    cfg = config or WorkflowLoggerConfig.load()
    if info is None:
        bundle = _fallback_bundle()
        token = _CURRENT_BUNDLE.set(bundle)
        try:
            yield bundle
        finally:
            _CURRENT_BUNDLE.reset(token)
        return

    workflow_id = _sanitize_component(getattr(info, "workflow_id", ""))
    run_id = _sanitize_component(getattr(info, "workflow_run_id", ""))
    activity_type = _sanitize_component(getattr(info, "activity_type", "activity"))
    activity_id = _sanitize_component(getattr(info, "activity_id", ""))
    attempt = getattr(info, "attempt", 0)

    base_dir = (
        cfg.log_root
        / workflow_id
        / run_id
        / "activities"
        / f"{activity_type}_{activity_id}_{attempt}"
    )
    activity_path = base_dir / "activity.log"
    devin_path = base_dir / "devin.log"

    activity_logger = _create_file_logger(
        "workflow.activity", activity_path, _parse_level(cfg.activity_level)
    )
    devin_logger = _create_file_logger(
        "workflow.devin", devin_path, _parse_level(cfg.devin_level)
    )

    bundle = _LogBundle(
        activity=activity_logger,
        devin=devin_logger,
        workflow=logging.getLogger("workflow.execution"),
        client=logging.getLogger("workflow.client"),
        artifact_dir=base_dir,
        activity_path=activity_path,
        devin_path=devin_path,
    )
    token = _CURRENT_BUNDLE.set(bundle)
    try:
        yield bundle
    finally:
        _CURRENT_BUNDLE.reset(token)
        _close_logger(activity_logger)
        _close_logger(devin_logger)


def get_activity_artifact_dir() -> Optional[Path]:
    bundle = _CURRENT_BUNDLE.get()
    return bundle.artifact_dir if bundle is not None else None


def get_activity_log_path() -> Optional[str]:
    bundle = _CURRENT_BUNDLE.get()
    if bundle is None or bundle.activity_path is None:
        return None
    return _relative_or_absolute(bundle.activity_path)


def get_devin_log_path() -> Optional[str]:
    bundle = _CURRENT_BUNDLE.get()
    if bundle is None or bundle.devin_path is None:
        return None
    return _relative_or_absolute(bundle.devin_path)


@contextmanager
def workflow_log_context(
    workflow_info: Any = None,
    config: WorkflowLoggerConfig | None = None,
) -> Iterator[logging.Logger]:
    info = _resolve_workflow_info(workflow_info)
    cfg = config or WorkflowLoggerConfig.load()
    if info is None:
        bundle = _fallback_bundle()
        token = _CURRENT_BUNDLE.set(bundle)
        try:
            yield bundle.workflow
        finally:
            _CURRENT_BUNDLE.reset(token)
        return

    workflow_id = _sanitize_component(getattr(info, "workflow_id", ""))
    run_id = _sanitize_component(getattr(info, "workflow_run_id", ""))
    base_dir = cfg.log_root / workflow_id / run_id
    workflow_path = base_dir / "workflow.log"

    workflow_logger = _create_file_logger(
        "workflow.execution", workflow_path, _parse_level(cfg.workflow_level)
    )

    bundle = _LogBundle(
        activity=logging.getLogger("workflow.activity"),
        devin=logging.getLogger("workflow.devin"),
        workflow=workflow_logger,
        client=logging.getLogger("workflow.client"),
        workflow_path=workflow_path,
    )
    token = _CURRENT_BUNDLE.set(bundle)
    try:
        yield workflow_logger
    finally:
        _CURRENT_BUNDLE.reset(token)
        _close_logger(workflow_logger)


def get_workflow_logger() -> logging.Logger:
    bundle = _CURRENT_BUNDLE.get()
    if bundle is None:
        return logging.getLogger("workflow.execution")
    return bundle.workflow


@contextmanager
def client_log_context(
    workflow_id: str,
    run_id: str = "",
    config: WorkflowLoggerConfig | None = None,
) -> Iterator[logging.Logger]:
    cfg = config or WorkflowLoggerConfig.load()
    sanitized_workflow_id = _sanitize_component(workflow_id)
    sanitized_run_id = _sanitize_component(run_id) if run_id else ""

    if sanitized_run_id:
        base_dir = cfg.log_root / sanitized_workflow_id / sanitized_run_id
    else:
        base_dir = cfg.log_root / sanitized_workflow_id
    client_path = base_dir / "client.log"

    client_logger = _create_file_logger(
        "workflow.client", client_path, _parse_level(cfg.client_level)
    )

    bundle = _LogBundle(
        activity=logging.getLogger("workflow.activity"),
        devin=logging.getLogger("workflow.devin"),
        workflow=logging.getLogger("workflow.execution"),
        client=client_logger,
        client_path=client_path,
    )
    token = _CURRENT_BUNDLE.set(bundle)
    try:
        yield client_logger
    finally:
        _CURRENT_BUNDLE.reset(token)
        _close_logger(client_logger)


def get_client_logger() -> logging.Logger:
    bundle = _CURRENT_BUNDLE.get()
    if bundle is None:
        return logging.getLogger("workflow.client")
    return bundle.client


def get_workflow_log_path() -> Optional[str]:
    bundle = _CURRENT_BUNDLE.get()
    if bundle is None or bundle.workflow_path is None:
        return None
    return _relative_or_absolute(bundle.workflow_path)


def get_client_log_path() -> Optional[str]:
    bundle = _CURRENT_BUNDLE.get()
    if bundle is None or bundle.client_path is None:
        return None
    return _relative_or_absolute(bundle.client_path)


def get_activity_logger() -> logging.Logger:
    bundle = _CURRENT_BUNDLE.get()
    if bundle is None:
        return logging.getLogger("workflow.activity")
    return bundle.activity


def get_devin_logger() -> logging.Logger:
    bundle = _CURRENT_BUNDLE.get()
    if bundle is None:
        return logging.getLogger("workflow.devin")
    return bundle.devin
