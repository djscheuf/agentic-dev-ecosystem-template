import pytest


@pytest.fixture(autouse=True)
def isolate_workflow_logs(monkeypatch, tmp_path):
    """Redirect per-execution workflow logs into a temporary directory."""
    monkeypatch.setenv("STORY_ANALYSIS_LOG_ROOT", str(tmp_path / "logs"))
