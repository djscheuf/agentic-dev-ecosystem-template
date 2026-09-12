"""Configuration for the Story Analysis Workflow client."""

import json
import os
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
from typing import Optional

from cadence.api.v1 import workflow_pb2

DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent / "domain-task-list-retry-config.json"

DEFAULT_DOMAIN = "story-analysis"
DEFAULT_TASK_LIST = "story-analysis"
DEFAULT_TARGET = "localhost:7833"


@dataclass(frozen=True)
class CadenceConfig:
    """Client-side Cadence configuration derived from the workstream config file."""

    domain: str
    task_list: str
    cadence_target: str
    execution_start_to_close_timeout: timedelta
    task_start_to_close_timeout: timedelta
    escalation_timeout: timedelta

    @classmethod
    def from_dict(cls, data: dict) -> "CadenceConfig":
        workflow_defaults = data.get("workflow_defaults", {})
        human_escalation = data.get("human_escalation", {})
        return cls(
            domain=data["domain"],
            task_list=data["task_list"],
            cadence_target=data["cadence_target"],
            execution_start_to_close_timeout=timedelta(
                seconds=workflow_defaults.get("execution_start_to_close_timeout_seconds", 3600)
            ),
            task_start_to_close_timeout=timedelta(
                seconds=workflow_defaults.get("task_start_to_close_timeout_seconds", 10)
            ),
            escalation_timeout=timedelta(seconds=human_escalation.get("timeout_seconds", 300)),
        )

    def to_start_workflow_kwargs(self, workflow_id: str) -> dict:
        """Return the option kwargs passed to ``client.start_workflow``."""
        return {
            "workflow_id": workflow_id,
            "task_list": self.task_list,
            "execution_start_to_close_timeout": self.execution_start_to_close_timeout,
            "task_start_to_close_timeout": self.task_start_to_close_timeout,
            "workflow_id_reuse_policy": workflow_pb2.WORKFLOW_ID_REUSE_POLICY_REJECT_DUPLICATE,
        }


def load_config(
    config_path: Optional[Path] = None,
    *,
    domain: Optional[str] = None,
    task_list: Optional[str] = None,
    cadence_target: Optional[str] = None,
    execution_start_to_close_timeout_seconds: Optional[int] = None,
    task_start_to_close_timeout_seconds: Optional[int] = None,
    escalation_timeout_seconds: Optional[int] = None,
) -> CadenceConfig:
    """Load Cadence client configuration with environment and override fallbacks.

    Order of precedence: explicit argument overrides > config file > environment
    variable > hardcoded defaults.
    """
    path = config_path or DEFAULT_CONFIG_PATH
    if path and path.exists():
        data = json.loads(path.read_text())
    else:
        data = {}

    data.setdefault("domain", os.environ.get("CADENCE_DOMAIN", DEFAULT_DOMAIN))
    data.setdefault("task_list", os.environ.get("CADENCE_TASK_LIST", DEFAULT_TASK_LIST))
    data.setdefault("cadence_target", os.environ.get("CADENCE_TARGET", DEFAULT_TARGET))

    if domain is not None:
        data["domain"] = domain
    if task_list is not None:
        data["task_list"] = task_list
    if cadence_target is not None:
        data["cadence_target"] = cadence_target

    workflow_defaults = data.setdefault("workflow_defaults", {})
    if execution_start_to_close_timeout_seconds is not None:
        workflow_defaults["execution_start_to_close_timeout_seconds"] = execution_start_to_close_timeout_seconds
    if task_start_to_close_timeout_seconds is not None:
        workflow_defaults["task_start_to_close_timeout_seconds"] = task_start_to_close_timeout_seconds

    human_escalation = data.setdefault("human_escalation", {})
    if escalation_timeout_seconds is not None:
        human_escalation["timeout_seconds"] = escalation_timeout_seconds

    return CadenceConfig.from_dict(data)
