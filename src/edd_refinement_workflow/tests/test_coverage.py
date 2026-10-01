import pytest
import yaml

from edd_refinement_workflow.coverage import CoverageCalculator


def test_coverage_calculator_marks_required_test_cases_and_invalidates_unknown(
    tmp_path,
) -> None:
    cases_path = tmp_path / "cases.yaml"
    cases_path.write_text(
        yaml.safe_dump(
            [
                {
                    "group": "Core",
                    "tests": [
                        {"id": "TC-001"},
                        {"id": "TC-002"},
                        {"id": "TC-003"},
                    ],
                }
            ]
        )
    )

    calculator = CoverageCalculator(cases_path)

    result = calculator.calculate(
        {"metadata": {"covers_test_case_ids": ["TC-001", "TC-002", "TC-999"]}},
        "metadata.covers_test_case_ids",
    )

    assert result["valid"] is False
    assert result["unknown"] == ["TC-999"]
    assert result["covered"] == ["TC-001", "TC-002"]
    assert result["uncovered"] == ["TC-003"]
    assert result["required_coverage"] == {
        "TC-001": 1,
        "TC-002": 1,
        "TC-003": 0,
    }


def test_coverage_calculator_returns_empty_for_missing_metadata_property(
    tmp_path,
) -> None:
    cases_path = tmp_path / "cases.yaml"
    cases_path.write_text(
        yaml.safe_dump(
            [{"group": "Core", "tests": [{"id": "TC-001"}]}]
        )
    )

    calculator = CoverageCalculator(cases_path)
    result = calculator.calculate({}, "metadata.covers_test_case_ids")

    assert result["valid"] is True
    assert result["covered"] == []
    assert result["uncovered"] == ["TC-001"]
    assert result["required_coverage"] == {"TC-001": 0}
