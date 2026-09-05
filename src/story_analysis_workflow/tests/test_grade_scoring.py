import pytest

from story_analysis_workflow.grade_scoring import score_analysis_grade


def _dim(score):
    return {"score": score, "reason": "", "recommendation": ""}


def test_score_analysis_grade_when_all_dimensions_max_returns_passed():
    grade = {
        "business_value": _dim(3),
        "scope": _dim(3),
        "acceptance_criteria": _dim(3),
        "story_format": _dim(3),
        "dependencies": _dim(3),
    }

    score_pct, passed = score_analysis_grade(grade)

    assert score_pct == 1.0
    assert passed is True


def test_score_analysis_grade_when_below_threshold_returns_not_passed():
    grade = {
        "business_value": _dim(1),
        "scope": _dim(1),
        "acceptance_criteria": _dim(1),
        "story_format": _dim(1),
        "dependencies": _dim(1),
    }

    score_pct, passed = score_analysis_grade(grade)

    assert score_pct == pytest.approx(1 / 3)
    assert passed is False


def test_score_analysis_grade_at_exact_threshold_returns_passed():
    # 12/15 = 80% exactly.
    grade = {
        "business_value": _dim(3),
        "scope": _dim(3),
        "acceptance_criteria": _dim(3),
        "story_format": _dim(3),
        "dependencies": _dim(0),
    }

    score_pct, passed = score_analysis_grade(grade)

    assert passed is True
