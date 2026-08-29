"""Unit tests for the ``repair-story-analysis`` SDLC skill Activity."""

import json

import pytest

from orchestrator.skill_activity import SkillActivityInput, run_skill
from tests.fake_harness import FakeHarness


def test_run_skill_repair_story_analysis_writes_repaired_analysis(tmp_path):
    harness = FakeHarness()
    skill_input = SkillActivityInput(
        skill_name="repair-story-analysis",
        input_paths=[".process/analysis.json", ".process/grade.json"],
        context="focus on edge cases and acceptance criteria",
    )

    output = run_skill(
        skill_input,
        output_path_key="analysis_path",
        repo_root=tmp_path,
        harness=harness,
    )

    assert output.status == "success"
    assert output.output_path == ".process/analysis.json"
    assert output.sentinel_path == ".process/repair-story-analysis.done.json"
    sentinel = json.loads((tmp_path / ".process" / "repair-story-analysis.done.json").read_text())
    assert sentinel["task"] == "repair-story-analysis"
    assert sentinel["verify_params"]["analysis_path"] == ".process/analysis.json"


def test_run_skill_repair_story_analysis_passes_context_in_prompt(tmp_path):
    class RecordingHarness(FakeHarness):
        def __init__(self):
            super().__init__()
            self.calls = []

        def run(self, prompt, *, cwd):
            self.calls.append(prompt)
            return super().run(prompt, cwd=cwd)

    harness = RecordingHarness()
    notes = "add more detail about the persona"
    skill_input = SkillActivityInput(
        skill_name="repair-story-analysis",
        input_paths=[".process/analysis.json", ".process/grade.json"],
        context=notes,
    )

    run_skill(
        skill_input,
        output_path_key="analysis_path",
        repo_root=tmp_path,
        harness=harness,
    )

    assert len(harness.calls) == 1
    assert notes in harness.calls[0]
