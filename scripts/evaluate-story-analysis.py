#!/usr/bin/env python3
"""Evaluate the artifacts produced by a Story Analysis Workflow run.

Given the `story-analysis.report.json` published for a completed run (see
`vault/decisions/ADR-016-consolidated-run-reporting.md`), this script proves
that every artifact the run claims to have produced actually exists, resolves
correctly relative to the repo root, and complies with its skill's schema:

  * The consolidated run report itself validates against
    `src/story_analysis_workflow/schemas/story-analysis-report-v1.schema.json`.
  * Every required Skill Activity (extract-story-intent, analyze-story,
    grade-story-analysis) left behind a sentinel file and a result file,
    even if the workflow looped back and re-ran analyze-story/
    grade-story-analysis one or more times (`repair_attempt_count`).
  * Each sentinel is structurally valid and its `verify_params` path matches
    the Activity's recorded `output_path`.
  * Each result file validates against the skill's JSON Schema
    (extract-story-intent/schema/story-intent.schema.json,
    analyze-story/schema/analysis.schema.json,
    grade-story-analysis/schema/analysis-grade.schema.json).
  * `story_document` and `final_analysis_path` (and every attempt's
    output/log paths) resolve to real files, whether given as an absolute
    path or one relative to the repo root.

Note: this deliberately does not invoke the skills' own `verify.sh` scripts.
Those are agentic controls (quantitative gates + grading thresholds wired into
the workflow itself, see ADR-005) rather than external proof that the
workflow's outputs are well-formed and resolvable, which is this script's job.

Usage:
    scripts/evaluate-story-analysis.py <target> [--output PATH]

`target` is typically the parent directory of the input story document (e.g.
`docs/ex2`, alongside its sentinels and result files) once
`story-analysis.report.json` for the run has been placed there. It also
accepts the report file directly, or a `.process/logs/<workflow_id>/<run_id>`
directory, or a `.process/logs/<workflow_id>` directory if it holds exactly
one run.

Exit status 0 if every check passes, 1 otherwise.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import jsonschema

REPO_ROOT = Path(__file__).resolve().parent.parent
REPORT_SCHEMA_PATH = REPO_ROOT / "src/story_analysis_workflow/schemas/story-analysis-report-v1.schema.json"
SKILLS_DIR = REPO_ROOT / ".devin/skills"

# step_name -> (verify_params key, output JSON Schema path)
SKILL_SPECS = {
    "extract-story-intent": (
        "extracted_intent_path",
        SKILLS_DIR / "extract-story-intent/schema/story-intent.schema.json",
    ),
    "analyze-story": (
        "analysis_path",
        SKILLS_DIR / "analyze-story/schema/analysis.schema.json",
    ),
    "grade-story-analysis": (
        "analysis_grade_path",
        SKILLS_DIR / "grade-story-analysis/schema/analysis-grade.schema.json",
    ),
    # repair-story-analysis has no dedicated skill folder: it rewrites the
    # same analysis.json, so it reuses analyze-story's schema.
    "repair-story-analysis": (
        "analysis_path",
        SKILLS_DIR / "analyze-story/schema/analysis.schema.json",
    ),
}

REQUIRED_STEPS = ("extract-story-intent", "analyze-story", "grade-story-analysis")

SENTINEL_SCHEMA = {
    "type": "object",
    "required": ["task", "status", "verify_params"],
    "properties": {
        "task": {"type": "string", "minLength": 1},
        "status": {"type": "string", "minLength": 1},
        "verify_params": {"type": "object"},
    },
}


@dataclass
class Check:
    id: str
    description: str
    passed: bool
    details: str = ""


@dataclass
class AttemptEval:
    sequence: int
    step_name: str
    attempt: int
    outcome: str
    output_path: str
    sentinel_path: Optional[str] = None
    checks: list[Check] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(check.passed for check in self.checks)


def resolve_path(value: str) -> Path:
    """Resolve a path the same way the runtime does: absolute paths are used
    as-is, everything else is resolved relative to the repo root."""
    path = Path(value)
    return path if path.is_absolute() else REPO_ROOT / path


def find_report_path(target: str) -> Path:
    path = Path(target).expanduser()
    if not path.is_absolute():
        path = (Path.cwd() / path).resolve()
    if path.is_file():
        return path
    if path.is_dir():
        direct = path / "story-analysis.report.json"
        if direct.is_file():
            return direct
        matches = sorted(path.rglob("story-analysis.report.json"))
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            listing = "\n".join(f"  - {m}" for m in matches)
            raise SystemExit(
                f"Multiple runs found under {path}; pass the exact run "
                f"directory or report path:\n{listing}"
            )
        raise SystemExit(f"No story-analysis.report.json found under {path}")
    raise SystemExit(f"Not a file or directory: {path}")


def validate_json_schema(document: dict, schema: dict) -> Optional[str]:
    """Return None if `document` matches `schema`, else an error message."""
    try:
        validator_cls = jsonschema.validators.validator_for(schema)
        validator_cls.check_schema(schema)
        validator = validator_cls(schema)
        errors = sorted(validator.iter_errors(document), key=lambda e: list(e.path))
    except jsonschema.SchemaError as exc:
        return f"invalid schema: {exc.message}"
    if not errors:
        return None
    return "; ".join(f"{'/'.join(str(p) for p in e.path) or '<root>'}: {e.message}" for e in errors[:10])


def check_path_exists(check_id: str, description: str, value: str) -> Check:
    resolved = resolve_path(value)
    exists = resolved.is_file()
    detail = str(resolved) if exists else f"missing: {resolved} (from {value!r})"
    return Check(check_id, description, exists, detail)


def load_json(path: Path) -> tuple[Optional[dict], Optional[str]]:
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except FileNotFoundError:
        return None, f"file not found: {path}"
    except json.JSONDecodeError as exc:
        return None, f"invalid JSON in {path}: {exc}"


def evaluate_attempt(attempt: dict, sentinel_dir_source: str) -> AttemptEval:
    step_name = attempt["step_name"]
    ev = AttemptEval(
        sequence=attempt["sequence"],
        step_name=step_name,
        attempt=attempt["attempt"],
        outcome=attempt["outcome"],
        output_path=attempt["output_path"],
    )

    for field_name in ("output_path", "activity_log_path", "devin_log_path"):
        value = attempt.get(field_name)
        if value:
            ev.checks.append(check_path_exists(field_name, f"{step_name}: {field_name} exists", value))
    if attempt.get("atif_path"):
        ev.checks.append(check_path_exists("atif_path", f"{step_name}: atif_path exists", attempt["atif_path"]))

    spec = SKILL_SPECS.get(step_name)
    if spec is None:
        ev.checks.append(Check("known_skill", f"{step_name}: recognized skill", False, "no schema mapping for this step_name"))
        return ev
    verify_key, schema_path = spec

    sentinel_dir = resolve_path(sentinel_dir_source).parent
    sentinel_path = sentinel_dir / ".process" / f"{step_name}.done.json"
    ev.sentinel_path = str(sentinel_path)

    sentinel_exists = sentinel_path.is_file()
    ev.checks.append(Check("sentinel_exists", f"{step_name}: sentinel file exists", sentinel_exists, str(sentinel_path)))
    if not sentinel_exists:
        return ev

    sentinel, err = load_json(sentinel_path)
    if err:
        ev.checks.append(Check("sentinel_json", f"{step_name}: sentinel is valid JSON", False, err))
        return ev

    sentinel_err = validate_json_schema(sentinel, SENTINEL_SCHEMA)
    ev.checks.append(Check("sentinel_schema", f"{step_name}: sentinel matches sentinel structure", sentinel_err is None, sentinel_err or ""))

    task_ok = sentinel.get("task") == step_name
    ev.checks.append(Check("sentinel_task", f"{step_name}: sentinel task matches step", task_ok, f"task={sentinel.get('task')!r}"))

    status = sentinel.get("status")
    status_ok = status not in (None, "failed", "ambiguity")
    ev.checks.append(Check("sentinel_status", f"{step_name}: sentinel status is terminal-success", status_ok, f"status={status!r}"))

    verify_params = sentinel.get("verify_params", {}) or {}
    verify_value = verify_params.get(verify_key)
    key_ok = bool(verify_value)
    ev.checks.append(Check("verify_params_key", f"{step_name}: verify_params.{verify_key} present", key_ok, f"{verify_key}={verify_value!r}"))

    if key_ok:
        consistent = resolve_path(verify_value) == resolve_path(attempt["output_path"])
        ev.checks.append(Check(
            "verify_params_matches_output",
            f"{step_name}: verify_params.{verify_key} matches attempt.output_path",
            consistent,
            f"{verify_value!r} vs {attempt['output_path']!r}",
        ))

    # Result file existence + formal JSON Schema compliance.
    output_check = check_path_exists("output_exists", f"{step_name}: output file exists", attempt["output_path"])
    ev.checks.append(output_check)
    if output_check.passed:
        schema, schema_err = load_json(schema_path)
        if schema_err:
            ev.checks.append(Check("output_schema", f"{step_name}: output matches {schema_path.name}", False, schema_err))
        else:
            document, doc_err = load_json(resolve_path(attempt["output_path"]))
            if doc_err:
                ev.checks.append(Check("output_schema", f"{step_name}: output matches {schema_path.name}", False, doc_err))
            else:
                schema_error = validate_json_schema(document, schema)
                ev.checks.append(Check("output_schema", f"{step_name}: output matches {schema_path.name}", schema_error is None, schema_error or ""))

    return ev


def evaluate(report_path: Path) -> dict:
    checks: list[Check] = []

    report, err = load_json(report_path)
    if err:
        raise SystemExit(err)

    report_schema, schema_err = load_json(REPORT_SCHEMA_PATH)
    if schema_err:
        raise SystemExit(schema_err)
    report_schema_error = validate_json_schema(report, report_schema)
    checks.append(Check("report_schema", "report matches story-analysis-report-v1.schema.json", report_schema_error is None, report_schema_error or ""))

    checks.append(check_path_exists("story_document", "story_document resolves and exists", report["story_document"]))

    final_status = report.get("final_status")
    final_analysis_path = report.get("final_analysis_path")
    if final_analysis_path is not None:
        checks.append(check_path_exists("final_analysis_path", "final_analysis_path resolves and exists", final_analysis_path))
    else:
        checks.append(Check(
            "final_analysis_path",
            "final_analysis_path present when the run reports success",
            final_status not in ("passed", "human_resolved"),
            f"final_status={final_status!r} but final_analysis_path is null",
        ))

    checks.append(Check("final_status_ok", "report final_status is a passing outcome", final_status in ("passed", "human_resolved"), f"final_status={final_status!r}"))

    attempts = sorted(report.get("attempts", []), key=lambda a: a["sequence"])
    attempt_evals: list[AttemptEval] = []
    sentinel_dir_source = report["story_document"]
    for attempt in attempts:
        step_name = attempt["step_name"]
        source = report["story_document"] if step_name == "extract-story-intent" else sentinel_dir_source
        attempt_eval = evaluate_attempt(attempt, source)
        attempt_evals.append(attempt_eval)
        sentinel_dir_source = attempt["output_path"]

    seen_steps = {a.step_name for a in attempt_evals}
    missing_steps = [s for s in REQUIRED_STEPS if s not in seen_steps]
    checks.append(Check(
        "required_steps_present",
        f"all required Skill Activities ran: {', '.join(REQUIRED_STEPS)}",
        not missing_steps,
        f"missing: {missing_steps}" if missing_steps else "",
    ))
    # `repair_attempt_count` counts REANALYZE loop iterations, where the
    # engine simply re-invokes `analyze-story` (see story_analysis_engine.py);
    # it does not imply a distinct `repair-story-analysis` step_name, so it's
    # informational only here, not a separate pass/fail gate.

    all_attempt_checks_passed = all(a.passed for a in attempt_evals)
    checks.append(Check("all_attempts_valid", "every attempt's sentinel + result file is valid", all_attempt_checks_passed, ""))

    overall_passed = all(c.passed for c in checks)

    return {
        "schema_version": "1.0",
        "evaluated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "report_path": str(report_path),
        "workflow_id": report.get("workflow_id"),
        "run_id": report.get("run_id"),
        "story_document": str(resolve_path(report["story_document"])),
        "final_analysis_path": str(resolve_path(final_analysis_path)) if final_analysis_path else None,
        "final_status_from_report": final_status,
        "usage": report.get("usage"),
        "checks": [check.__dict__ for check in checks],
        "attempts": [
            {
                "sequence": a.sequence,
                "step_name": a.step_name,
                "attempt": a.attempt,
                "outcome": a.outcome,
                "output_path": a.output_path,
                "sentinel_path": a.sentinel_path,
                "passed": a.passed,
                "checks": [check.__dict__ for check in a.checks],
            }
            for a in attempt_evals
        ],
        "final_status": "passed" if overall_passed else "failed",
    }


def print_summary(evaluation: dict) -> None:
    print(f"Evaluating report: {evaluation['report_path']}")
    print(f"  workflow_id={evaluation['workflow_id']} run_id={evaluation['run_id']}")
    for check in evaluation["checks"]:
        mark = "PASS" if check["passed"] else "FAIL"
        print(f"  [{mark}] {check['description']}" + (f" -- {check['details']}" if check["details"] and not check["passed"] else ""))
    for attempt in evaluation["attempts"]:
        mark = "PASS" if attempt["passed"] else "FAIL"
        print(f"  [{mark}] attempt seq={attempt['sequence']} step={attempt['step_name']}")
        for check in attempt["checks"]:
            if not check["passed"]:
                print(f"        [FAIL] {check['description']} -- {check['details']}")
    usage = evaluation.get("usage") or {}
    usage_bits = ", ".join(
        f"{k}={v.get('value')}" for k, v in usage.items() if isinstance(v, dict)
    )
    print(f"  usage: {usage_bits}")
    print(f"Final status: {evaluation['final_status'].upper()}")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("target", help="story-analysis.report.json path, its run directory, or a workflow-id directory with exactly one run")
    parser.add_argument("--output", help="Where to write the evaluation report JSON (default: alongside the input report as story-analysis.eval.json)")
    args = parser.parse_args(argv)

    report_path = find_report_path(args.target)
    evaluation = evaluate(report_path)
    print_summary(evaluation)

    output_path = Path(args.output).expanduser() if args.output else report_path.with_name("story-analysis.eval.json")
    output_path.write_text(json.dumps(evaluation, indent=2) + "\n", encoding="utf-8")
    print(f"Evaluation report written to {output_path}")

    return 0 if evaluation["final_status"] == "passed" else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
