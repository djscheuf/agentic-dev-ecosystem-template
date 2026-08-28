"""Human-escalation types shared by the pure engine and the Cadence workflow.

Kept free of any Cadence import so it can be unit tested directly.
"""

from dataclasses import dataclass
from enum import Enum


class EscalationReason(str, Enum):
    GRADE_REPAIR_EXHAUSTED = "grade_repair_exhausted"
    ACTIVITY_FLAGGED_AMBIGUITY = "activity_flagged_ambiguity"
    ACTIVITY_FAILURE_EXHAUSTED_RETRIES = "activity_failure_exhausted_retries"


class HumanDecision(str, Enum):
    RETRY = "retry"
    ACCEPT = "accept"
    ABORT = "abort"


@dataclass(frozen=True)
class EscalationState:
    reason: EscalationReason
    attempt_count: int
    awaiting_signal: bool = True


@dataclass(frozen=True)
class HumanResponse:
    decision: HumanDecision
    notes: str = ""


def parse_human_response(decision: str, notes: str = "") -> HumanResponse:
    try:
        parsed_decision = HumanDecision(decision)
    except ValueError as exc:
        raise ValueError(f"Unknown human_response decision: {decision!r}") from exc
    return HumanResponse(decision=parsed_decision, notes=notes)
