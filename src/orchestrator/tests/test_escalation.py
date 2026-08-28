import pytest

from orchestrator.escalation import (
    EscalationReason,
    HumanDecision,
    parse_human_response,
)


def test_parse_human_response_with_retry_decision_returns_retry():
    response = parse_human_response("retry", notes="try again with more detail")

    assert response.decision == HumanDecision.RETRY
    assert response.notes == "try again with more detail"


def test_parse_human_response_with_accept_decision_returns_accept():
    response = parse_human_response("accept")

    assert response.decision == HumanDecision.ACCEPT
    assert response.notes == ""


def test_parse_human_response_with_abort_decision_returns_abort():
    response = parse_human_response("abort")

    assert response.decision == HumanDecision.ABORT


def test_parse_human_response_with_unknown_decision_raises_value_error():
    with pytest.raises(ValueError):
        parse_human_response("maybe-later")


def test_escalation_reason_values_match_instrumentation_contract():
    assert EscalationReason.GRADE_REPAIR_EXHAUSTED.value == "grade_repair_exhausted"
    assert EscalationReason.ACTIVITY_FLAGGED_AMBIGUITY.value == "activity_flagged_ambiguity"
    assert (
        EscalationReason.ACTIVITY_FAILURE_EXHAUSTED_RETRIES.value
        == "activity_failure_exhausted_retries"
    )
