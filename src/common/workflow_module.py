from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class WorkflowModuleSpec:
    name: str
    domain: str
    task_list: str
    workflow_types: tuple[str, ...]
    activity_types: tuple[str, ...]
    register: Callable[[object], None]
