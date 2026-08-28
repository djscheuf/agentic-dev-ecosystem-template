from orchestrator.grade_repair import (
    GradeRepairDecision,
    GradeRepairState,
    evaluate_grade_repair,
)


def test_evaluate_grade_repair_when_passed_returns_proceed():
    state = GradeRepairState(attempt_count=0, max_attempts=3)

    decision = evaluate_grade_repair(passed=True, state=state)

    assert decision == GradeRepairDecision.PROCEED


def test_evaluate_grade_repair_when_failed_below_max_attempts_returns_repair():
    state = GradeRepairState(attempt_count=2, max_attempts=3)

    decision = evaluate_grade_repair(passed=False, state=state)

    assert decision == GradeRepairDecision.REPAIR


def test_evaluate_grade_repair_when_failed_at_max_attempts_returns_escalate():
    state = GradeRepairState(attempt_count=3, max_attempts=3)

    decision = evaluate_grade_repair(passed=False, state=state)

    assert decision == GradeRepairDecision.ESCALATE


def test_evaluate_grade_repair_when_failed_above_max_attempts_returns_escalate():
    state = GradeRepairState(attempt_count=5, max_attempts=3)

    decision = evaluate_grade_repair(passed=False, state=state)

    assert decision == GradeRepairDecision.ESCALATE
