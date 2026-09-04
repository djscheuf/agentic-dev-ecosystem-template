from dataclasses import dataclass

from .workflow_module import WorkflowModuleSpec


@dataclass(frozen=True)
class WorkerSpec:
    domain: str
    task_list: str
    cadence_target: str
    modules: tuple[WorkflowModuleSpec, ...]
