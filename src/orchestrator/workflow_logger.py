"""Workflow-aware file logging compatibility API for the orchestrator.

Provides per-execution loggers for the worker, workflow, client, activity,
and devin subprocess output. Log directories are derived from the Cadence
execution context (``activity.info()`` / ``workflow.WorkflowContext``) or
from explicit identifiers passed by clients.

Usage from an Activity::

    from orchestrator.workflow_logger import activity_log_context, get_activity_logger

    with activity_log_context():
        get_activity_logger().debug("doing work")

Usage from the workflow engine::

    from orchestrator.workflow_logger import workflow_log_context, get_workflow_logger

    with workflow_log_context():
        get_workflow_logger().info("workflow step")

Usage from a client::

    from orchestrator.workflow_logger import client_log_context, get_client_logger

    with client_log_context(workflow_id, run_id):
        get_client_logger().info("sent signal")
"""

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
except ImportError:  # pragma: no cover
    activity = None  # type: ignore[var-annotated]

try:
    from cadence.workflow import WorkflowContext
except ImportError:  # pragma: no cover
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


@dataclass(frozen=True)
class WorkflowLoggerConfig:
    """File-based configuration for workflow logging."""

    log_root: Path = DEFAULT_LOG_ROOT
    worker_level: str = DEFAULT_LEVELS["worker"]
    workflow_level: str = DEFAULT_LEVELS["workflow"]
    client_level: str = DEFAULT_LEVELS["client"]
    activity_level: str = DEFAULT_LEVELS["activity"]
    devin_level: str = DEFAULT_LEVELS["devin"]

    @classmethod
    def load(cls, config_path: Path = DEFAULT_CONFIG_PATH) -> "WorkflowLoggerConfig":
        """Load config from ``config_path`` (if it exists) and apply env overrides.

        ``STORY_ANALYSIS_LOG_ROOT`` overrides ``log_root`` so tests and operators
        can redirect logs without editing the config file.
        """
        if config_path.exists():
            data = json.loads(config_path.read_text())
        else:
            data = {}

        levels = data.get("levels", {})
        log_root_raw = os.environ.get(
            "STORY_ANALYSIS_LOG_ROOT",
            data.get("log_root", str(DEFAULT_LOG_ROOT)),
        )
        log_root = Path(log_root_raw)
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
    activity_path: Optional[Path] = None
    devin_path: Optional[Path] = None
    workflow_path: Optional[Path] = None
    client_path: Optional[Path] = None


_CURRENT_BUNDLE: ContextVar[Optional[_LogBundle]] = ContextVar(
    "orchestrator_log_bundle", default=None
)


def _sanitize_component(value: str) -> str:
    """Make a workflow/run/activity identifier safe to use as a path component."""
    sanitized = _SAFE_COMPONENT_RE.sub("_", value).strip("_")
    return sanitized or "unknown"


def _parse_level(value: Any) -> int:
    """Convert a level name or integer to a logging level."""
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        parsed = logging.getLevelName(value.upper())
        if isinstance(parsed, int):
            return parsed
    return logging.INFO


def _logger_name_from_path(base: str, path: Path) -> str:
    """Create a unique logger name derived from the log file path."""
    suffix = re.sub(r"[^A-Za-z0-9_]+", "_", str(path)).strip("_")
    return f"{base}.{suffix}"


def _create_file_logger(name: str, path: Path, level: int) -> logging.Logger:
    """Create a logger that writes plain-text records to ``path``."""
    path.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger(_logger_name_from_path(name, path))
    logger.setLevel(level)
    logger.handlers = []
    handler = logging.FileHandler(path)
    handler.setLevel(level)
    handler.setFormatter(logging.Formatter(LOG_FORMAT))
    logger.addHandler(handler)
    logger.propagate = False
    return logger


def _close_logger(logger: logging.Logger) -> None:
    """Close and remove all handlers from a logger."""
    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        handler.close()


def _null_logger(name: str) -> logging.Logger:
    """Return a logger that silently drops records.

    Used as a fallback when code asks for a workflow/activity/devin logger
    outside of a logging context.
    """
    logger = logging.getLogger(f"orchestrator.fallback.{name}")
    if not logger.handlers:
        logger.addHandler(logging.NullHandler())
    logger.propagate = False
    return logger


def _fallback_bundle() -> _LogBundle:
    return _LogBundle(
        activity=_null_logger("activity"),
        devin=_null_logger("devin"),
        workflow=_null_logger("workflow"),
        client=_null_logger("client"),
    )


def _relative_or_absolute(path: Path) -> str:
    """Return a repo-relative path when possible, otherwise an absolute path."""
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def get_config() -> WorkflowLoggerConfig:
    """Return the current logging configuration."""
    return WorkflowLoggerConfig.load()


def get_activity_logger() -> logging.Logger:
    """Return the activity logger for the current logging context."""
    bundle = _CURRENT_BUNDLE.get(None)
    if bundle is None:
        return _null_logger("activity")
    return bundle.activity


def get_devin_logger() -> logging.Logger:
    """Return the devin subprocess logger for the current logging context."""
    bundle = _CURRENT_BUNDLE.get(None)
    if bundle is None:
        return _null_logger("devin")
    return bundle.devin


def get_workflow_logger() -> logging.Logger:
    """Return the workflow logger for the current logging context."""
    bundle = _CURRENT_BUNDLE.get(None)
    if bundle is None:
        return _null_logger("workflow")
    return bundle.workflow


def get_client_logger() -> logging.Logger:
    """Return the client logger for the current logging context."""
    bundle = _CURRENT_BUNDLE.get(None)
    if bundle is None:
        return _null_logger("client")
    return bundle.client


def get_activity_log_path() -> Optional[str]:
    """Return the path of the current activity log, or ``None``."""
    bundle = _CURRENT_BUNDLE.get(None)
    if bundle is None or bundle.activity_path is None:
        return None
    return _relative_or_absolute(bundle.activity_path)


def get_devin_log_path() -> Optional[str]:
    """Return the path of the current devin log, or ``None``."""
    bundle = _CURRENT_BUNDLE.get(None)
    if bundle is None or bundle.devin_path is None:
        return None
    return _relative_or_absolute(bundle.devin_path)


def get_workflow_log_path() -> Optional[str]:
    """Return the path of the current workflow log, or ``None``."""
    bundle = _CURRENT_BUNDLE.get(None)
    if bundle is None or bundle.workflow_path is None:
        return None
    return _relative_or_absolute(bundle.workflow_path)


def get_client_log_path() -> Optional[str]:
    """Return the path of the current client log, or ``None``."""
    bundle = _CURRENT_BUNDLE.get(None)
    if bundle is None or bundle.client_path is None:
        return None
    return _relative_or_absolute(bundle.client_path)


def _resolve_activity_info(activity_info: Any = None) -> Any:
    """Use an explicit info object, ``activity.info()``, or ``None``."""
    if activity_info is not None:
        return activity_info
    if activity is not None and activity.in_activity():
        return activity.info()
    return None


def _resolve_workflow_info(workflow_info: Any = None) -> Any:
    """Use an explicit info object, ``WorkflowContext.get().info()``, or ``None``."""
    if workflow_info is not None:
        return workflow_info
    if WorkflowContext is not None and WorkflowContext.is_set():
        return WorkflowContext.get().info()
    return None


@contextmanager
def activity_log_context(
    activity_info: Any = None,
    config: Optional[WorkflowLoggerConfig] = None,
) -> Iterator[_LogBundle]:
    """Open an activity-scoped logging context.

    Creates ``activity.log`` and ``devin.log`` under
    ``<log_root>/<workflow_id>/<run_id>/activities/<activity_type>_<activity_id>_<attempt>/``.

    ``activity_info`` is intended for tests; production callers should leave it
    ``None`` so the context reads from ``cadence.activity.info()``.
    """
    info = _resolve_activity_info(activity_info)
    cfg = config or get_config()
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
        "orchestrator.activity", activity_path, _parse_level(cfg.activity_level)
    )
    devin_logger = _create_file_logger(
        "orchestrator.devin", devin_path, _parse_level(cfg.devin_level)
    )

    bundle = _LogBundle(
        activity=activity_logger,
        devin=devin_logger,
        workflow=_null_logger("workflow"),
        client=_null_logger("client"),
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


@contextmanager
def workflow_log_context(
    workflow_info: Any = None,
    config: Optional[WorkflowLoggerConfig] = None,
) -> Iterator[_LogBundle]:
    """Open a workflow-scoped logging context.

    Creates ``workflow.log`` under ``<log_root>/<workflow_id>/<run_id>/``.

    ``workflow_info`` is intended for tests; production callers should leave it
    ``None`` so the context reads from ``cadence.workflow.WorkflowContext``.
    """
    info = _resolve_workflow_info(workflow_info)
    cfg = config or get_config()
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
    base_dir = cfg.log_root / workflow_id / run_id
    workflow_path = base_dir / "workflow.log"

    workflow_logger = _create_file_logger(
        "orchestrator.workflow", workflow_path, _parse_level(cfg.workflow_level)
    )

    bundle = _LogBundle(
        activity=_null_logger("activity"),
        devin=_null_logger("devin"),
        workflow=workflow_logger,
        client=_null_logger("client"),
        workflow_path=workflow_path,
    )
    token = _CURRENT_BUNDLE.set(bundle)
    try:
        yield bundle
    finally:
        _CURRENT_BUNDLE.reset(token)
        _close_logger(workflow_logger)


@contextmanager
def client_log_context(
    workflow_id: str,
    run_id: str = "",
    config: Optional[WorkflowLoggerConfig] = None,
) -> Iterator[_LogBundle]:
    """Open a client-scoped logging context.

    Creates ``client.log`` under ``<log_root>/<workflow_id>/<run_id>/`` when
    ``run_id`` is provided, otherwise under ``<log_root>/<workflow_id>/``.
    """
    cfg = config or get_config()
    sanitized_workflow_id = _sanitize_component(workflow_id)
    sanitized_run_id = _sanitize_component(run_id) if run_id else ""

    if sanitized_run_id:
        base_dir = cfg.log_root / sanitized_workflow_id / sanitized_run_id
    else:
        base_dir = cfg.log_root / sanitized_workflow_id
    client_path = base_dir / "client.log"

    client_logger = _create_file_logger(
        "orchestrator.client", client_path, _parse_level(cfg.client_level)
    )

    bundle = _LogBundle(
        activity=_null_logger("activity"),
        devin=_null_logger("devin"),
        workflow=_null_logger("workflow"),
        client=client_logger,
        client_path=client_path,
    )
    token = _CURRENT_BUNDLE.set(bundle)
    try:
        yield bundle
    finally:
        _CURRENT_BUNDLE.reset(token)
        _close_logger(client_logger)


def setup_worker_logging(config: Optional[WorkflowLoggerConfig] = None) -> None:
    """Configure the root logger for the worker process.

    The worker startup script redirects stdout/stderr to ``scripts/.run/worker.log``,
    so this function only sets the level and formatter; it does not add a second
    file handler.
    """
    cfg = config or get_config()
    level = _parse_level(cfg.worker_level)
    root = logging.getLogger()
    if not root.handlers:
        logging.basicConfig(level=level, format=LOG_FORMAT)
    else:
        root.setLevel(level)
        for handler in root.handlers:
            if isinstance(handler, logging.StreamHandler):
                handler.setFormatter(logging.Formatter(LOG_FORMAT))


def get_worker_logger() -> logging.Logger:
    """Return the worker logger.

    Logs from this logger propagate to the root logger, which the worker startup
    script captures in ``scripts/.run/worker.log``.
    """
    logger = logging.getLogger("orchestrator.worker")
    if not logger.handlers:
        logger.addHandler(logging.NullHandler())
    return logger
