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

    def __post_init__(self) -> None:
        for field_name in ("name", "domain", "task_list"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip() or value != value.strip():
                raise ValueError(f"{field_name} must be a non-empty trimmed string")
