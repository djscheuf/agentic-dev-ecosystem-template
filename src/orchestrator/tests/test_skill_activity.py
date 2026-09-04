import json
from pathlib import Path
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


def test_execute_with_successful_sentinel_completes_fixed_lifecycle(tmp_path):
    from orchestrator.skill_activity import SkillActivity

    events = []
    config_path = tmp_path / "probe.config.json"
    config_path.write_text(
        json.dumps(
            {
                "activity": {
                    "skill_name": "probe-skill",
                    "output_path_key": "probe_path",
                },
                "harness": {"alternate": {"nested": ["value"]}},
            }
        )
    )

    class RecordingContext:
        def __init__(self, wrapped):
            self.wrapped = wrapped

        def __enter__(self):
            events.append("context_enter")
            return self.wrapped.__enter__()

        def __exit__(self, exc_type, exc_value, traceback):
            try:
                return self.wrapped.__exit__(exc_type, exc_value, traceback)
            finally:
                events.append("context_exit")

    class RecordingHarness:
        def run(self, prompt, *, cwd, config):
            events.append("harness")
            assert get_current_skill_name() == "probe-skill"
            assert config["alternate"]["nested"] == ("value",)
            _write_sentinel(
                cwd,
                "probe-skill",
                verify_params={"probe_path": "docs/probe.json"},
            )
            return HarnessResult(exit_code=0, stdout="", stderr="")

    class RecordingActivity(SkillActivity):
        def expected_output_path(self, skill_input):
            return tmp_path / "fallback.json"

        def modify_sentinel_path(self, sentinel_path):
            events.append("sentinel")
            return sentinel_path

        def modify_prompt(self, prompt):
            events.append("prompt")
            return prompt

        def modify_harness_config(self, config):
            events.append("config")
            return config

        def modify_invocation_context(self, context):
            events.append("context")
            return RecordingContext(context)

        def modify_output_path(self, output_path):
            events.append("output")
            return output_path

        def modify_result(self, result):
            events.append("result")
            return result

    activity = RecordingActivity(
        config_path=config_path,
        harness=RecordingHarness(),
        repo_root=tmp_path,
    )

    output = activity.execute(SkillActivityInput(skill_name="ignored"))

    assert events == [
        "sentinel",
        "prompt",
        "config",
        "context",
        "context_enter",
        "harness",
        "context_exit",
        "output",
        "result",
    ]
    assert output.output_path == "docs/probe.json"
    assert get_current_skill_name() is None


def test_adapters_with_concrete_activities_preserve_output_and_config_contracts():
    from orchestrator.activities.analyze_story import ANALYZE_STORY_ACTIVITY
    from orchestrator.activities.extract_story_intent import EXTRACT_STORY_INTENT_ACTIVITY
    from orchestrator.activities.grade_story_analysis import GRADE_STORY_ANALYSIS_ACTIVITY
    from orchestrator.activities.repair_story_analysis import REPAIR_STORY_ANALYSIS_ACTIVITY

    cases = [
        (
            EXTRACT_STORY_INTENT_ACTIVITY,
            SkillActivityInput("ignored", ["docs/story.md"]),
            "docs/story.intent.json",
        ),
        (
            ANALYZE_STORY_ACTIVITY,
            SkillActivityInput("ignored", ["docs/story.intent.json"]),
            "docs/story.analysis.json",
        ),
        (
            GRADE_STORY_ANALYSIS_ACTIVITY,
            SkillActivityInput("ignored", ["docs/story.analysis.json"]),
            "docs/story.analysis-grade.json",
        ),
        (
            REPAIR_STORY_ANALYSIS_ACTIVITY,
            SkillActivityInput("ignored", ["docs/story.analysis.json"]),
            "docs/story.analysis.json",
        ),
    ]

    assert [
        (
            activity.skill_name,
            str(activity.expected_output_path(skill_input)),
            activity.harness_config["devin"]["permission_mode"],
        )
        for activity, skill_input, expected_path in cases
    ] == [
        (activity.skill_name, expected_path, "accept-edits")
        for activity, skill_input, expected_path in cases
    ]


def test_load_with_invalid_adjacent_config_fails_sanitized(tmp_path, monkeypatch):
    from orchestrator.skill_activity_config import SkillActivityConfig

    malformed = tmp_path / "malformed.config.json"
    malformed.write_text("{")
    wrong_type = tmp_path / "wrong-type.config.json"
    wrong_type.write_text("[]")
    incomplete = tmp_path / "incomplete.config.json"
    incomplete.write_text(
        json.dumps({"activity": {"skill_name": "probe"}, "harness": {}})
    )
    unreadable = tmp_path / "unreadable.config.json"
    unreadable.write_text("{}")
    original_read_text = type(unreadable).read_text

    def read_text(path, *args, **kwargs):
        if path == unreadable:
            raise PermissionError("sensitive operating-system detail")
        return original_read_text(path, *args, **kwargs)

    monkeypatch.setattr(type(unreadable), "read_text", read_text)
    cases = [
        (tmp_path / "missing.config.json", "missing_file: missing.config.json"),
        (unreadable, "unreadable_file: unreadable.config.json"),
        (malformed, "malformed_json: malformed.config.json"),
        (wrong_type, "invalid_type: root"),
        (incomplete, "missing_field: activity.output_path_key"),
    ]

    errors = []
    for config_path, expected in cases:
        with pytest.raises(ValueError) as error:
            SkillActivityConfig.load(config_path)
        errors.append(str(error.value))

    assert errors == [expected for config_path, expected in cases]
    assert "sensitive operating-system detail" not in " ".join(errors)


def test_execute_with_invalid_harness_or_hook_result_fails_clearly(tmp_path):
    from orchestrator.skill_activity import SkillActivity

    config_path = tmp_path / "probe.config.json"
    config_path.write_text(
        json.dumps(
            {
                "activity": {
                    "skill_name": "probe-skill",
                    "output_path_key": "probe_path",
                },
                "harness": {},
            }
        )
    )

    class ProbeActivity(SkillActivity):
        def expected_output_path(self, skill_input):
            return tmp_path / "fallback.json"

    class ValidHarness:
        def run(self, prompt, *, cwd, config):
            _write_sentinel(
                cwd,
                "probe-skill",
                verify_params={"probe_path": "docs/probe.json"},
            )
            return HarnessResult(exit_code=0, stdout="", stderr="")

    boundaries = [
        "modify_sentinel_path",
        "modify_prompt",
        "modify_harness_config",
        "modify_invocation_context",
        "modify_output_path",
        "modify_result",
    ]
    errors = []
    for boundary in boundaries:
        activity = ProbeActivity(
            config_path=config_path,
            harness=ValidHarness(),
            repo_root=tmp_path,
        )
        setattr(activity, boundary, lambda value: object())
        with pytest.raises(SkillActivityError) as error:
            activity.execute(SkillActivityInput(skill_name="ignored"))
        errors.append(str(error.value))

    class InvalidHarness:
        def run(self, prompt, *, cwd, config):
            return object()

    activity = ProbeActivity(
        config_path=config_path,
        harness=InvalidHarness(),
        repo_root=tmp_path,
    )
    with pytest.raises(SkillActivityError) as error:
        activity.execute(SkillActivityInput(skill_name="ignored"))
    errors.append(str(error.value))

    assert errors == [
        *(f"invalid_hook_return_type: {boundary}" for boundary in boundaries),
        "invalid_harness_result",
    ]


def test_execute_with_nonzero_harness_result_fails_without_sensitive_output(tmp_path):
    from orchestrator.skill_activity import SkillActivity

    config_path = tmp_path / "probe.config.json"
    config_path.write_text(
        json.dumps(
            {
                "activity": {
                    "skill_name": "probe-skill",
                    "output_path_key": "probe_path",
                },
                "harness": {"alternate": {"token": "sensitive-config"}},
            }
        )
    )
    calls = []
    events = []

    class ProbeActivity(SkillActivity):
        def expected_output_path(self, skill_input):
            return tmp_path / "fallback.json"

    class FailingHarness:
        def run(self, prompt, *, cwd, config):
            calls.append((prompt, config))
            return HarnessResult(
                exit_code=17,
                stdout="sensitive-stdout",
                stderr="sensitive-stderr",
            )

    logger = SimpleNamespace(
        error=lambda message, *args: events.append(message % args),
        info=lambda *args: None,
        warning=lambda *args: None,
        debug=lambda *args: None,
    )
    activity = ProbeActivity(
        config_path=config_path,
        harness=FailingHarness(),
        repo_root=tmp_path,
    )

    with patch("orchestrator.skill_activity.get_activity_logger", return_value=logger):
        with pytest.raises(SkillActivityError) as error:
            activity.execute(
                SkillActivityInput(
                    skill_name="ignored", context="sensitive-prompt"
                )
            )

    assert len(calls) == 1
    assert str(error.value) == "Harness exited 17 while running skill 'probe-skill'"
    assert events == [
        "FailSkillHarnessInvocation: skill_name=probe-skill exit_code=17"
    ]
    assert all(
        marker not in " ".join(events) + str(error.value)
        for marker in (
            "sensitive-stdout",
            "sensitive-stderr",
            "sensitive-prompt",
            "sensitive-config",
        )
    )


def test_execute_with_stale_sentinel_removes_before_harness(tmp_path):
    from orchestrator.skill_activity import SkillActivity

    config_path = tmp_path / "probe.config.json"
    config_path.write_text(
        json.dumps(
            {
                "activity": {
                    "skill_name": "probe-skill",
                    "output_path_key": "probe_path",
                },
                "harness": {},
            }
        )
    )
    _write_sentinel(
        tmp_path,
        "probe-skill",
        verify_params={"probe_path": "docs/stale.json"},
    )
    sentinel_path = tmp_path / ".process" / "probe-skill.done.json"

    class ProbeActivity(SkillActivity):
        def expected_output_path(self, skill_input):
            return tmp_path / "fallback.json"

    class RecordingHarness:
        def run(self, prompt, *, cwd, config):
            assert not sentinel_path.exists()
            _write_sentinel(
                cwd,
                "probe-skill",
                verify_params={"probe_path": "docs/fresh.json"},
            )
            return HarnessResult(exit_code=0, stdout="", stderr="")

    output = ProbeActivity(
        config_path=config_path,
        harness=RecordingHarness(),
        repo_root=tmp_path,
    ).execute(SkillActivityInput(skill_name="ignored"))

    assert output.output_path == "docs/fresh.json"


def test_execute_with_missing_sentinel_uses_concrete_fallback_and_warns(tmp_path):
    from orchestrator.activities import analyze_story as module

    events = []

    class SuccessfulHarness:
        def run(self, prompt, *, cwd, config):
            return HarnessResult(exit_code=0, stdout="", stderr="")

    logger = SimpleNamespace(
        warning=lambda message, *args: events.append(message % args),
        error=lambda *args: None,
        info=lambda *args: None,
        debug=lambda *args: None,
    )
    activity = module.AnalyzeStorySkillActivity(
        config_path=Path(module.__file__).with_suffix(".config.json"),
        harness=SuccessfulHarness(),
        repo_root=tmp_path,
    )

    with patch("orchestrator.skill_activity.get_activity_logger", return_value=logger):
        output = activity.execute(
            SkillActivityInput(
                skill_name="ignored", input_paths=["docs/story.intent.json"]
            )
        )

    assert output.output_path == "docs/story.analysis.json"
    assert events == [
        "WarnSkillArtifactVerification: skill_name=analyze-story "
        "failure_reason=missing_sentinel output_path=docs/story.analysis.json"
    ]


def test_execute_with_invalid_present_sentinel_fails_strictly(tmp_path):
    from orchestrator.skill_activity import SkillActivity

    config_path = tmp_path / "probe.config.json"
    config_path.write_text(
        json.dumps(
            {
                "activity": {
                    "skill_name": "probe-skill",
                    "output_path_key": "probe_path",
                },
                "harness": {},
            }
        )
    )

    class ProbeActivity(SkillActivity):
        def expected_output_path(self, skill_input):
            return tmp_path / "fallback.json"

    class SentinelHarness:
        def __init__(self, sentinel):
            self.sentinel = sentinel

        def run(self, prompt, *, cwd, config):
            sentinel_path = cwd / ".process" / "probe-skill.done.json"
            sentinel_path.parent.mkdir(parents=True, exist_ok=True)
            sentinel_path.write_text(
                self.sentinel
                if isinstance(self.sentinel, str)
                else json.dumps(self.sentinel)
            )
            return HarnessResult(exit_code=0, stdout="", stderr="")

    cases = [
        ("{", "Malformed sentinel for skill 'probe-skill'"),
        (
            {"task": "other-skill", "verify_params": {"probe_path": "out.json"}},
            "Sentinel task mismatch for skill 'probe-skill'",
        ),
        (
            {"task": "probe-skill", "verify_params": {}},
            "Sentinel for skill 'probe-skill' is missing verify_params.probe_path",
        ),
    ]
    errors = []
    for sentinel, expected in cases:
        activity = ProbeActivity(
            config_path=config_path,
            harness=SentinelHarness(sentinel),
            repo_root=tmp_path,
        )
        with pytest.raises(SkillActivityError) as error:
            activity.execute(SkillActivityInput(skill_name="ignored"))
        errors.append(str(error.value))

    assert errors == [expected for sentinel, expected in cases]
