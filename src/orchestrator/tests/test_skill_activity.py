import json

import pytest

from orchestrator.harness import HarnessResult
from orchestrator.skill_activity import (
    SkillActivityError,
    SkillActivityInput,
    run_skill,
)


def _write_sentinel(repo_root, skill_name, task=None, verify_params=None):
    process_dir = repo_root / ".process"
    process_dir.mkdir(parents=True, exist_ok=True)
    sentinel = {
        "task": task if task is not None else skill_name,
        "verify_params": verify_params if verify_params is not None else {},
    }
    (process_dir / f"{skill_name}.done.json").write_text(json.dumps(sentinel))


class FakeHarness:
    """Records the prompt it was asked to run and returns a canned result.

    `on_run`, when given, lets a test simulate the harness's agent doing its
    work (e.g. writing the skill's sentinel file) as part of the call.
    """

    def __init__(self, exit_code=0, stdout="", stderr="", on_run=None):
        self.exit_code = exit_code
        self.stdout = stdout
        self.stderr = stderr
        self.calls = []
        self._on_run = on_run

    def run(self, prompt, *, cwd):
        self.calls.append({"prompt": prompt, "cwd": cwd})
        if self._on_run is not None:
            self._on_run(prompt, cwd)
        return HarnessResult(exit_code=self.exit_code, stdout=self.stdout, stderr=self.stderr)


def test_run_skill_on_success_returns_output_path_from_sentinel(tmp_path):
    def on_run(prompt, cwd):
        _write_sentinel(
            tmp_path, "extract-story-intent", verify_params={"extracted_intent_path": "docs/foo.intent.json"}
        )

    skill_input = SkillActivityInput(skill_name="extract-story-intent", input_paths=["docs/foo.md"])

    output = run_skill(
        skill_input,
        output_path_key="extracted_intent_path",
        repo_root=tmp_path,
        harness=FakeHarness(on_run=on_run),
    )

    assert output.status == "success"
    assert output.output_path == "docs/foo.intent.json"


def test_run_skill_when_harness_exits_non_zero_raises_skill_activity_error(tmp_path):
    skill_input = SkillActivityInput(skill_name="extract-story-intent", input_paths=["docs/foo.md"])

    with pytest.raises(SkillActivityError):
        run_skill(
            skill_input,
            output_path_key="extracted_intent_path",
            repo_root=tmp_path,
            harness=FakeHarness(exit_code=1, stderr="boom"),
        )


def test_run_skill_when_sentinel_missing_raises_skill_activity_error(tmp_path):
    skill_input = SkillActivityInput(skill_name="extract-story-intent", input_paths=["docs/foo.md"])

    with pytest.raises(SkillActivityError):
        run_skill(
            skill_input,
            output_path_key="extracted_intent_path",
            repo_root=tmp_path,
            harness=FakeHarness(),
        )


def test_run_skill_when_sentinel_task_mismatched_raises_skill_activity_error(tmp_path):
    def on_run(prompt, cwd):
        _write_sentinel(
            tmp_path,
            "extract-story-intent",
            task="some-other-skill",
            verify_params={"extracted_intent_path": "docs/foo.intent.json"},
        )

    skill_input = SkillActivityInput(skill_name="extract-story-intent", input_paths=["docs/foo.md"])

    with pytest.raises(SkillActivityError):
        run_skill(
            skill_input,
            output_path_key="extracted_intent_path",
            repo_root=tmp_path,
            harness=FakeHarness(on_run=on_run),
        )


def test_run_skill_when_retried_removes_stale_sentinel_first(tmp_path):
    # Simulate a stale sentinel left over from a previous (crashed) attempt,
    # pointing at a different output than the retry will produce.
    _write_sentinel(
        tmp_path,
        "extract-story-intent",
        verify_params={"extracted_intent_path": "docs/stale.intent.json"},
    )

    def on_run(prompt, cwd):
        # The harness's agent is responsible for (re)writing the sentinel;
        # our fake mimics that by writing the fresh one as part of the call.
        _write_sentinel(
            tmp_path,
            "extract-story-intent",
            verify_params={"extracted_intent_path": "docs/fresh.intent.json"},
        )

    skill_input = SkillActivityInput(skill_name="extract-story-intent", input_paths=["docs/foo.md"])

    output = run_skill(
        skill_input,
        output_path_key="extracted_intent_path",
        repo_root=tmp_path,
        harness=FakeHarness(on_run=on_run),
    )

    assert output.output_path == "docs/fresh.intent.json"


def test_run_skill_passes_unicode_story_text_unmodified_in_prompt(tmp_path):
    def on_run(prompt, cwd):
        _write_sentinel(
            tmp_path, "extract-story-intent", verify_params={"extracted_intent_path": "docs/foo.intent.json"}
        )

    unicode_text = "So that I can ship faster \u2014 caf\u00e9 \U0001F680"
    skill_input = SkillActivityInput(
        skill_name="extract-story-intent",
        input_paths=[],
        context=unicode_text,
    )
    harness = FakeHarness(on_run=on_run)

    run_skill(
        skill_input,
        output_path_key="extracted_intent_path",
        repo_root=tmp_path,
        harness=harness,
    )

    assert unicode_text in harness.calls[0]["prompt"]


def test_run_skill_sends_prompt_to_the_given_harness_rooted_at_repo_root(tmp_path):
    def on_run(prompt, cwd):
        _write_sentinel(
            tmp_path, "extract-story-intent", verify_params={"extracted_intent_path": "docs/foo.intent.json"}
        )

    skill_input = SkillActivityInput(skill_name="extract-story-intent", input_paths=["docs/foo.md"])
    harness = FakeHarness(on_run=on_run)

    run_skill(
        skill_input,
        output_path_key="extracted_intent_path",
        repo_root=tmp_path,
        harness=harness,
    )

    assert len(harness.calls) == 1
    assert harness.calls[0]["cwd"] == tmp_path
    assert "extract-story-intent" in harness.calls[0]["prompt"]
    assert "docs/foo.md" in harness.calls[0]["prompt"]
