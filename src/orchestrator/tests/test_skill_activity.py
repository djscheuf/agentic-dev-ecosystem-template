import json
from types import SimpleNamespace

import pytest

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


def _fake_runner(returncode=0, stdout="", stderr="", writes_sentinel=None):
    """Build a fake subprocess runner.

    `writes_sentinel`, when given, is a `(repo_root, skill_name, verify_params)`
    tuple written to the sentinel file as part of the "subprocess" call, mirroring
    how the real `devin` CLI invocation writes it before exiting (ADR-004).
    """

    def runner(*args, **kwargs):
        if writes_sentinel is not None:
            repo_root, skill_name, verify_params = writes_sentinel
            _write_sentinel(repo_root, skill_name, verify_params=verify_params)
        return SimpleNamespace(returncode=returncode, stdout=stdout, stderr=stderr)

    return runner


def test_run_skill_on_success_returns_output_path_from_sentinel(tmp_path):
    skill_input = SkillActivityInput(skill_name="extract-story-intent", input_paths=["docs/foo.md"])

    output = run_skill(
        skill_input,
        output_path_key="extracted_intent_path",
        repo_root=tmp_path,
        runner=_fake_runner(
            returncode=0,
            writes_sentinel=(tmp_path, "extract-story-intent", {"extracted_intent_path": "docs/foo.intent.json"}),
        ),
    )

    assert output.status == "success"
    assert output.output_path == "docs/foo.intent.json"


def test_run_skill_when_devin_exits_non_zero_raises_skill_activity_error(tmp_path):
    skill_input = SkillActivityInput(skill_name="extract-story-intent", input_paths=["docs/foo.md"])

    with pytest.raises(SkillActivityError):
        run_skill(
            skill_input,
            output_path_key="extracted_intent_path",
            repo_root=tmp_path,
            runner=_fake_runner(returncode=1, stderr="boom"),
        )


def test_run_skill_when_sentinel_missing_raises_skill_activity_error(tmp_path):
    skill_input = SkillActivityInput(skill_name="extract-story-intent", input_paths=["docs/foo.md"])

    with pytest.raises(SkillActivityError):
        run_skill(
            skill_input,
            output_path_key="extracted_intent_path",
            repo_root=tmp_path,
            runner=_fake_runner(returncode=0),
        )


def test_run_skill_when_sentinel_task_mismatched_raises_skill_activity_error(tmp_path):
    skill_input = SkillActivityInput(skill_name="extract-story-intent", input_paths=["docs/foo.md"])

    with pytest.raises(SkillActivityError):
        run_skill(
            skill_input,
            output_path_key="extracted_intent_path",
            repo_root=tmp_path,
            runner=lambda *a, **k: (
                _write_sentinel(
                    tmp_path,
                    "extract-story-intent",
                    task="some-other-skill",
                    verify_params={"extracted_intent_path": "docs/foo.intent.json"},
                )
                or SimpleNamespace(returncode=0, stdout="", stderr="")
            ),
        )


def test_run_skill_when_retried_removes_stale_sentinel_first(tmp_path):
    # Simulate a stale sentinel left over from a previous (crashed) attempt,
    # pointing at a different output than the retry will produce.
    _write_sentinel(
        tmp_path,
        "extract-story-intent",
        verify_params={"extracted_intent_path": "docs/stale.intent.json"},
    )

    def runner(*args, **kwargs):
        # The devin CLI subprocess is responsible for (re)writing the sentinel;
        # our fake mimics that by writing the fresh one before "exiting".
        _write_sentinel(
            tmp_path,
            "extract-story-intent",
            verify_params={"extracted_intent_path": "docs/fresh.intent.json"},
        )
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    skill_input = SkillActivityInput(skill_name="extract-story-intent", input_paths=["docs/foo.md"])

    output = run_skill(
        skill_input,
        output_path_key="extracted_intent_path",
        repo_root=tmp_path,
        runner=runner,
    )

    assert output.output_path == "docs/fresh.intent.json"


def test_run_skill_passes_unicode_story_text_unmodified_in_prompt(tmp_path):
    captured = {}

    def runner(command, **kwargs):
        captured["command"] = command
        _write_sentinel(
            tmp_path,
            "extract-story-intent",
            verify_params={"extracted_intent_path": "docs/foo.intent.json"},
        )
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    unicode_text = "So that I can ship faster \u2014 caf\u00e9 \U0001F680"
    skill_input = SkillActivityInput(
        skill_name="extract-story-intent",
        input_paths=[],
        context=unicode_text,
    )

    run_skill(
        skill_input,
        output_path_key="extracted_intent_path",
        repo_root=tmp_path,
        runner=runner,
    )

    assert unicode_text in captured["command"][-1]
