from dataclasses import dataclass

from .workflow_module import WorkflowModuleSpec


@dataclass(frozen=True)
class WorkerSpec:
    domain: str
    task_list: str
    cadence_target: str
    modules: tuple[WorkflowModuleSpec, ...]

    def __post_init__(self) -> None:
        for field_name in ("domain", "task_list", "cadence_target"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip() or value != value.strip():
                raise ValueError(f"{field_name} must be a non-empty trimmed string")
