"""Pure decision logic for the grade/repair loop (bounded to `max_attempts`).

Kept free of any Cadence import so it can be unit tested directly and reused
by both the pure `StoryAnalysisEngine` and the real Cadence workflow.
"""

from dataclasses import dataclass
from enum import Enum

DEFAULT_MAX_ATTEMPTS = 3


class GradeRepairDecision(str, Enum):
    PROCEED = "proceed"
    REPAIR = "repair"
    ESCALATE = "escalate"


@dataclass(frozen=True)
class GradeRepairState:
    attempt_count: int = 0
    max_attempts: int = DEFAULT_MAX_ATTEMPTS


def evaluate_grade_repair(passed: bool, state: GradeRepairState) -> GradeRepairDecision:
    if passed:
        return GradeRepairDecision.PROCEED
    if state.attempt_count < state.max_attempts:
        return GradeRepairDecision.REPAIR
    return GradeRepairDecision.ESCALATE
