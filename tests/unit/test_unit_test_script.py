from pathlib import Path


def test_unit_test_script_includes_common_suite() -> None:
    script = (Path(__file__).resolve().parents[2] / "scripts" / "run_unit_tests.sh").read_text()

    assert "src/common/tests" in script
