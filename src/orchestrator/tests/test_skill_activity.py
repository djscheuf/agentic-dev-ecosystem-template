import json
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from orchestrator.devin_harness import DevinHarness, DevinHarnessConfig
from orchestrator.harness import HarnessResult
from orchestrator.invocation_context import get_current_skill_name
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


def test_run_skill_exposes_canonical_skill_without_changing_harness_contract(tmp_path):
    observed = []

    def on_run(prompt, cwd):
        observed.append(get_current_skill_name())
        _write_sentinel(tmp_path, "analyze-story", verify_params={"analysis_path": "docs/foo.analysis.json"})

    output = run_skill(
        SkillActivityInput(skill_name="analyze-story"),
        output_path_key="analysis_path",
        harness=FakeHarness(on_run=on_run),
        repo_root=tmp_path,
    )

    assert observed == ["analyze-story"]
    assert output.output_path == "docs/foo.analysis.json"
    assert get_current_skill_name() is None


def test_run_skill_resets_invocation_context_after_harness_failure(tmp_path):
    observed = []

    class FailingHarness:
        def run(self, prompt, *, cwd):
            observed.append(get_current_skill_name())
            raise RuntimeError("boom")

    with pytest.raises(RuntimeError, match="boom"):
        run_skill(
            SkillActivityInput(skill_name="repair-story-analysis"),
            output_path_key="analysis_path",
            harness=FailingHarness(),
            repo_root=tmp_path,
        )

    assert observed == ["repair-story-analysis"]
    assert get_current_skill_name() is None


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


def test_run_skill_when_sentinel_missing_warns_and_uses_conventional_output_path(tmp_path):
    logger = SimpleNamespace(
        debug=lambda *args: None,
        info=lambda *args: None,
        warning_calls=[],
    )
    logger.warning = lambda message, *args: logger.warning_calls.append(message % args)
    skill_input = SkillActivityInput(skill_name="extract-story-intent", input_paths=["docs/foo.md"])

    with patch("orchestrator.skill_activity.get_activity_logger", new=lambda: logger):
        output = run_skill(
            skill_input,
            output_path_key="extracted_intent_path",
            repo_root=tmp_path,
            harness=FakeHarness(),
        )

    assert output.output_path == "docs/foo.intent.json"
    assert "missing_sentinel" in logger.warning_calls[0]


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


def test_run_skill_does_not_log_prompt_or_input_paths(tmp_path):
    class ListLogger:
        def __init__(self):
            self.records = []

        def debug(self, msg, *args):
            self.records.append(msg % args if args else msg)

        def info(self, msg, *args):
            self.records.append(msg % args if args else msg)

        def error(self, msg, *args):
            self.records.append("ERROR: " + (msg % args if args else msg))

    logger = ListLogger()

    def on_run(prompt, cwd):
        _write_sentinel(
            tmp_path, "extract-story-intent", verify_params={"extracted_intent_path": "docs/foo.intent.json"}
        )

    skill_input = SkillActivityInput(
        skill_name="extract-story-intent",
        input_paths=["docs/story.md"],
        context="sensitive prompt content",
    )

    with patch("orchestrator.skill_activity.get_activity_logger", new=lambda: logger):
        run_skill(
            skill_input,
            output_path_key="extracted_intent_path",
            repo_root=tmp_path,
            harness=FakeHarness(on_run=on_run),
        )

    full_log = "\n".join(logger.records)
    assert "sensitive prompt content" not in full_log
    assert "docs/story.md" not in full_log
    assert "extract-story-intent" in full_log


def test_run_skill_logs_missing_sentinel_warning(tmp_path):
    class ListLogger:
        def __init__(self):
            self.records = []

        def debug(self, msg, *args):
            self.records.append(msg % args if args else msg)

        def info(self, msg, *args):
            self.records.append(msg % args if args else msg)

        def warning(self, msg, *args):
            self.records.append("WARNING: " + (msg % args if args else msg))

    logger = ListLogger()
    skill_input = SkillActivityInput(
        skill_name="extract-story-intent", input_paths=["docs/story.md"]
    )

    with patch("orchestrator.skill_activity.get_activity_logger", new=lambda: logger):
        run_skill(
            skill_input,
            output_path_key="extracted_intent_path",
            repo_root=tmp_path,
            harness=FakeHarness(),
        )

    full_log = "\n".join(logger.records)
    assert "WarnSkillArtifactVerification" in full_log
    assert "extract-story-intent" in full_log
    assert "missing_sentinel" in full_log


def test_run_skill_with_authentication_failure_logs_sanitized_failure(tmp_path):
    class ListLogger:
        def __init__(self):
            self.records = []

        def debug(self, msg, *args):
            self.records.append(msg % args if args else msg)

        def info(self, msg, *args):
            self.records.append(msg % args if args else msg)

        def error(self, msg, *args):
            self.records.append("ERROR: " + (msg % args if args else msg))

    logger = ListLogger()
    harness = FakeHarness(
        exit_code=1,
        stderr="Not logged in: credential-marker",
    )

    with patch("orchestrator.skill_activity.get_activity_logger", new=lambda: logger):
        with pytest.raises(SkillActivityError):
            run_skill(
                SkillActivityInput(skill_name="analyze-story"),
                output_path_key="analysis_path",
                repo_root=tmp_path,
                harness=harness,
            )

    full_log = "\n".join(logger.records)
    assert "FailSkillHarnessInvocation" in full_log
    assert "skill_name=analyze-story" in full_log
    assert "exit_code=1" in full_log
    assert "credential-marker" not in full_log


def test_run_skill_with_auto_and_missing_sentinel_fails_without_escalation(tmp_path):
    commands = []

    def runner(command, **kwargs):
        commands.append(command)
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    harness = DevinHarness(config=DevinHarnessConfig(), runner=runner)

    with pytest.raises(SkillActivityError, match="Cannot derive output path"):
        run_skill(
            SkillActivityInput(skill_name="unconfigured-writer"),
            output_path_key="artifact_path",
            repo_root=tmp_path,
            harness=harness,
        )

    assert len(commands) == 1
    assert commands[0][commands[0].index("--permission-mode") + 1] == "auto"


def test_run_skill_for_each_story_analysis_skill_uses_configured_profile_and_artifact_contract(
    tmp_path,
):
    output_keys = {
        "extract-story-intent": "extracted_intent_path",
        "analyze-story": "analysis_path",
        "grade-story-analysis": "analysis_grade_path",
        "repair-story-analysis": "analysis_path",
    }
    commands = []

    def runner(command, **kwargs):
        skill_name = get_current_skill_name()
        output_path = f"docs/{skill_name}.json"
        _write_sentinel(
            tmp_path,
            skill_name,
            verify_params={output_keys[skill_name]: output_path},
        )
        commands.append(command)
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    harness = DevinHarness(runner=runner)

    outputs = {
        skill_name: run_skill(
            SkillActivityInput(skill_name=skill_name),
            output_path_key=output_key,
            repo_root=tmp_path,
            harness=harness,
        )
        for skill_name, output_key in output_keys.items()
    }

    assert [output.output_path for output in outputs.values()] == [
        f"docs/{skill_name}.json" for skill_name in output_keys
    ]
    assert len(commands) == 4
    for command in commands:
        assert command[command.index("--model") + 1] == "SWE-1.7"
        assert command[command.index("--permission-mode") + 1] == "accept-edits"


def test_load_with_valid_adjacent_config_returns_immutable_snapshot(tmp_path):
    from orchestrator.skill_activity_config import SkillActivityConfig

    config_path = tmp_path / "probe.config.json"
    config_path.write_text(
        json.dumps(
            {
                "activity": {
                    "skill_name": "probe-skill",
                    "output_path_key": "probe_path",
                },
                "harness": {
                    "devin": {
                        "model": "SWE-1.7",
                        "permission_mode": "accept-edits",
                        "options": ["first", {"nested": ["value"]}],
                    }
                },
            }
        )
    )

    loaded = SkillActivityConfig.load(config_path)
    config_path.write_text("{}")

    assert loaded.skill_name == "probe-skill"
    assert loaded.output_path_key == "probe_path"
    assert loaded.harness["devin"]["options"] == (
        "first",
        loaded.harness["devin"]["options"][1],
    )
    assert loaded.harness["devin"]["options"][1]["nested"] == ("value",)
    with pytest.raises(TypeError):
        loaded.harness["devin"]["model"] = "changed"
    with pytest.raises(TypeError):
        loaded.harness["devin"]["options"][1]["nested"] = ()
