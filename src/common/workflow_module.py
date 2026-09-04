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
        if not isinstance(self.name, str) or not self.name.strip() or self.name != self.name.strip():
            raise ValueError("name must be a non-empty trimmed string")
