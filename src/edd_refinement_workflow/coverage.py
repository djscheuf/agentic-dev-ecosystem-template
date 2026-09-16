from pathlib import Path

import yaml


class CoverageError(Exception):
    """Raised when a coverage calculation cannot be performed."""


class CoverageCalculator:
    """Compute required test-case coverage from an evaluation result.

    The calculator loads a YAML test-case catalog, extracts the set of
    required test-case IDs, then compares it against the IDs found at the
    dotted ``coverage_metadata_property`` path in an evaluation result.

    A result that references any ID not present in the catalog is considered
    invalid (unknown IDs).  The ``required_coverage`` map reports ``1`` for
    each required test case that is covered and ``0`` otherwise, which is the
    shape expected by the quality ratchet.
    """

    def __init__(self, test_cases_path: Path) -> None:
        self._required_ids = self._load_required_ids(Path(test_cases_path))

    @staticmethod
    def _load_required_ids(path: Path) -> set[str]:
        if not path.exists():
            raise CoverageError(f"test cases file not found: {path}")
        try:
            with path.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as exc:
            raise CoverageError(f"malformed test cases YAML: {exc}") from exc

        required_ids: set[str] = set()
        groups = data if isinstance(data, list) else [data] if isinstance(data, dict) else []
        for group in groups:
            if not isinstance(group, dict):
                continue
            tests = group.get("tests", []) if isinstance(group, dict) else []
            for test in tests:
                if isinstance(test, dict) and "id" in test:
                    required_ids.add(str(test["id"]))
        return required_ids

    @staticmethod
    def _extract_covered_ids(result: dict, property_path: str) -> list[str]:
        parts = property_path.split(".") if property_path else []
        value = result
        for part in parts:
            if not isinstance(value, dict) or part not in value:
                return []
            value = value[part]

        if isinstance(value, list):
            return [str(item) for item in value]
        if isinstance(value, str):
            return [value]
        return []

    def calculate(self, result: dict, coverage_metadata_property: str) -> dict:
        covered = self._extract_covered_ids(result, coverage_metadata_property)
        covered_set = set(covered)
        unknown = sorted(covered_set - self._required_ids)
        valid_ids = covered_set & self._required_ids
        uncovered = sorted(self._required_ids - valid_ids)
        required_coverage = {
            case_id: (1 if case_id in valid_ids else 0)
            for case_id in sorted(self._required_ids)
        }
        return {
            "required_coverage": required_coverage,
            "covered": sorted(valid_ids),
            "uncovered": uncovered,
            "unknown": unknown,
            "valid": not unknown,
        }
