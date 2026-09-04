"""Score an `analysis-grade.json` document against the fixed-floor pass threshold.

Per ADR-006 (Grader Skill Pattern) and `.devin/skills/grade-story-analysis/rubric.md`:
each of the 5 dimensions is scored 0-3, and the analysis passes if the total score
is at least `PASS_THRESHOLD` (80%) of the maximum possible.
"""

PASS_THRESHOLD = 0.8
MAX_SCORE_PER_DIMENSION = 3
DIMENSIONS = (
    "business_value",
    "scope",
    "acceptance_criteria",
    "story_format",
    "dependencies",
)


def score_analysis_grade(grade_document: dict) -> tuple[float, bool]:
    """Return `(score_pct, passed)` for a parsed analysis-grade.json document."""
    total = sum(grade_document.get(dimension, {}).get("score", 0) for dimension in DIMENSIONS)
    max_total = len(DIMENSIONS) * MAX_SCORE_PER_DIMENSION
    score_pct = total / max_total if max_total else 0.0
    return score_pct, score_pct >= PASS_THRESHOLD
