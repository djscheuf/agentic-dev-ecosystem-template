"""Test harness that simulates the four SDLC skill Activities.

Used by the integration and E2E test suites.  The harness writes the skill
sentinel files and artifact JSON that the real ``run_skill`` function expects,
without invoking the ``devin`` CLI.

Behaviour is controlled through environment variables so that the same harness
class can be used by a worker subprocess started with different test scenarios:

* ``STORY_ANALYSIS_GRADE_RESULTS`` - JSON list of booleans.  Each call to the
  ``grade-story-analysis`` skill consumes the next value; the last value repeats.
* ``STORY_ANALYSIS_FAIL_SKILLS`` - JSON list of skill names that should fail.
"""

import json
import os
import re
from pathlib import Path

from orchestrator.harness import HarnessResult


def _dim(score):
    return {"score": score, "reason": "", "recommendation": ""}


def _make_grade_document(passed: bool) -> dict:
    score = 3 if passed else 0
    return {
        "business_value": _dim(score),
        "scope": _dim(score),
        "acceptance_criteria": _dim(score),
        "story_format": _dim(score),
        "dependencies": _dim(score),
    }


class FakeHarness:
    """``Harness`` implementation that simulates skill execution for tests."""

    def __init__(self):
        self.grade_results = self._parse_bool_list("STORY_ANALYSIS_GRADE_RESULTS", [True])
        self.fail_skills = self._parse_str_list("STORY_ANALYSIS_FAIL_SKILLS", [])
        self._grade_call_count = 0

    @staticmethod
    def _parse_bool_list(env_var: str, default: list) -> list:
        raw = os.environ.get(env_var)
        if not raw:
            return list(default)
        return [bool(v) for v in json.loads(raw)]

    @staticmethod
    def _parse_str_list(env_var: str, default: list) -> list:
        raw = os.environ.get(env_var)
        if not raw:
            return list(default)
        return [str(v) for v in json.loads(raw)]

    def _next_grade_passed(self) -> bool:
        if self._grade_call_count < len(self.grade_results):
            result = self.grade_results[self._grade_call_count]
        else:
            result = self.grade_results[-1]
        self._grade_call_count += 1
        return result

    @staticmethod
    def _parse_skill_name(prompt: str) -> str:
        match = re.search(r"Invoke the '([^']+)' skill", prompt)
        if not match:
            raise ValueError(f"Could not parse skill name from prompt: {prompt!r}")
        return match.group(1)

    @staticmethod
    def _parse_first_input(prompt: str) -> str | None:
        match = re.search(r"Input document path\(s\): ([^,\n]+)", prompt)
        return match.group(1).strip() if match else None

    _FALLBACK_OUTPUTS = {
        "extract-story-intent": ".process/intent.json",
        "analyze-story": ".process/analysis.json",
        "grade-story-analysis": ".process/analysis-grade.json",
        "repair-story-analysis": ".process/analysis.json",
    }

    @staticmethod
    def _output_file_for_skill(skill_name: str, first_input: str | None) -> str:
        if first_input is None:
            return FakeHarness._FALLBACK_OUTPUTS[skill_name]
        input_path = Path(first_input)
        parent = input_path.parent
        name = input_path.name
        if skill_name == "extract-story-intent":
            base = re.sub(r"\.[^.]+$", "", name)
            new_name = f"{base}.intent.json"
        elif skill_name == "analyze-story":
            if name.endswith(".intent.json"):
                base = name[: -len(".intent.json")]
                new_name = f"{base}.analysis.json" if base else "analysis.json"
            else:
                new_name = "analysis.json"
        elif skill_name == "grade-story-analysis":
            if name.endswith(".analysis.json"):
                base = name[: -len(".analysis.json")]
                new_name = f"{base}.analysis-grade.json" if base else "analysis-grade.json"
            else:
                new_name = "analysis-grade.json"
        elif skill_name == "repair-story-analysis":
            # Repair overwrites the analysis file it is given.
            new_name = name
        else:
            raise ValueError(f"Unknown skill: {skill_name}")
        return str(parent / new_name)

    @staticmethod
    def _output_path_key(skill_name: str) -> str:
        mapping = {
            "extract-story-intent": "extracted_intent_path",
            "analyze-story": "analysis_path",
            "grade-story-analysis": "analysis_grade_path",
            "repair-story-analysis": "analysis_path",
        }
        return mapping[skill_name]

    def run(self, prompt: str, *, cwd: Path) -> HarnessResult:
        skill_name = self._parse_skill_name(prompt)

        if skill_name in self.fail_skills:
            return HarnessResult(exit_code=1, stdout="", stderr=f"Simulated {skill_name} failure")

        first_input = self._parse_first_input(prompt)
        output_file = self._output_file_for_skill(skill_name, first_input)
        output_path = Path(cwd) / output_file
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if skill_name == "grade-story-analysis":
            passed = self._next_grade_passed()
            output_path.write_text(json.dumps(_make_grade_document(passed)))
        else:
            output_path.write_text(json.dumps({}))

        sentinel = {
            "task": skill_name,
            "verify_params": {self._output_path_key(skill_name): output_file},
        }
        sentinel_path = Path(cwd) / ".process" / f"{skill_name}.done.json"
        sentinel_path.parent.mkdir(parents=True, exist_ok=True)
        sentinel_path.write_text(json.dumps(sentinel))

        return HarnessResult(exit_code=0, stdout="", stderr="")
