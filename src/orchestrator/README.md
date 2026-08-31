# Story Analysis Workflow (Cadence, Python client)

A working example of the SDLC Story Analysis Workflow — `extract-story-intent` ->
`analyze-story` -> `grade-story-analysis` <-> `repair-story-analysis` (bounded to 3
attempts) — implemented as a durable Cadence Workflow. See
`docs/reqs/workflow-orchestration/implement-story-analysis-workflow-example.design.json`
for the full design and `docs/reqs/workflow-orchestration/workflow-engine.test-plan.md`
for the test plan.

## Layout

| File | Purpose |
|---|---|
| `grade_repair.py` | Pure `evaluate_grade_repair()` decision function (proceed/repair/escalate). |
| `escalation.py` | `EscalationReason` / `HumanDecision` / `HumanResponse` types. |
| `grade_scoring.py` | Scores an `analysis-grade.json` against the ADR-006 pass threshold. |
| `harness.py` | `Harness` Protocol + `HarnessResult` — the pluggable backend that executes a skill prompt. |
| `devin_harness.py` | `DevinHarness`, the default `Harness`: shells out to the `devin` CLI. File-based config via `devin_harness.config.json` (model, permission_mode). |
| `skill_activity.py` | Connects a skill + inputs to a prompt and sends it to a given `Harness`; reads the sentinel it writes. |
| `story_analysis_engine.py` | `StoryAnalysisEngine` — all sequencing/decision logic, framework-independent. |
| `workflow.py` | `StoryAnalysisWorkflow`, the `@registry.workflow()` class wiring the engine to Cadence. |
| `single_activity_workflow.py` | `SingleActivityWorkflow`, a minimal probe workflow that schedules exactly one Activity — backs `scripts/run-single-activity` for manual activity-by-activity testing against a real Cadence server. |
| `activities/harness_instance.py` | The single shared `Harness` instance (`DevinHarness()`) the four Activities use — swap it here to use a different harness. |
| `activities/*.py` | The four `@activity.defn()` Activities. |
| `worker.py` | Registers `StoryAnalysisWorkflow`, `SingleActivityWorkflow`, and the four Activities; polls the `story-analysis` task list. |
| `tests/` | Unit tests for everything except the Cadence glue itself (see below). |

## Swapping the Harness

`skill_activity.run_skill()` takes any object implementing the `Harness` Protocol
(`harness.py`): a `run(prompt: str, *, cwd: Path) -> HarnessResult` method. To use a
different agent CLI/runtime instead of `devin`, implement that Protocol and point
`activities/harness_instance.py`'s `HARNESS` at your implementation — no changes
needed in `skill_activity.py` or any of the four Activities. Tests use a `FakeHarness`
(see `tests/test_skill_activity.py`) that records the prompt it was sent instead of
running a real subprocess.

## Why the logic is split into a pure engine

`cadence-python-client` 0.3.0 (latest release on PyPI as of this writing) does not
ship the `cadence.testing.TestWorkflowEnvironment` in-memory test harness yet (it
exists on the project's `main` branch, unreleased — see
`vault/services/cadence.md`). To keep this example fully unit tested without
depending on an unreleased SDK version or a live Cadence server, all of the
grade-repair-loop and human-escalation sequencing logic lives in
`StoryAnalysisEngine` (`story_analysis_engine.py`), which takes the four skill
calls, the human-response waiter, and timeouts as constructor arguments and never
imports `cadence`. `workflow.py` is a thin adapter that wires this engine to real
`execute_activity` / `sleep` / `wait_condition` calls.

## Running it against a real Cadence server

1. Bring up the local Cadence stack and register the domain — see
   `docs/reqs/workflow-orchestration/local-dev-prerequisites.md`.
2. Install dependencies (from the repo root, inside the Nix dev shell so
   `LD_LIBRARY_PATH` picks up `libstdc++.so.6` for `grpcio` — see `shell.nix`):
   ```bash
   nix-shell --run "python3 -m venv .venv && .venv/bin/pip install -r src/orchestrator/requirements.txt"
   ```
3. Start the Worker (from the repo root, with `src` on `PYTHONPATH`):
   ```bash
   nix-shell --run "PYTHONPATH=src .venv/bin/python -m orchestrator.worker"
   ```
4. In another terminal, start a workflow:
   ```bash
   cadence --domain story-analysis workflow start \
     --et 3600 \
     --tl story-analysis \
     --workflow_type StoryAnalysisWorkflow \
     --input '["docs/reqs/workflow-orchestration/story.md", {"max_attempts": 3}]' \
     --workflow_id "story-analysis-example"
   ```
5. Inspect progress with `cadence workflow describe` / `cadence workflow query
   --query_type get_status`, and respond to an escalation with:
   ```bash
   cadence --domain story-analysis workflow signal \
     --workflow_id "story-analysis-example" \
     --signal_name human_response \
     --input '{"decision":"accept","notes":"Looks good"}'
   ```

See `docs/reqs/workflow-orchestration/local-dev-prerequisites.md` for the full
prerequisites, gotchas, and payload-size/idempotency notes.

## Testing a single Activity in isolation

To exercise one Activity at a time against a real Cadence server (real retries,
timeouts, and task-list routing -- not an in-process/mocked call), bring the
engine up with `scripts/start-workflow-engine.sh`, then:

```bash
scripts/run-single-activity extract_story_intent docs/reqs/workflow-orchestration/story.md
scripts/run-single-activity analyze_story docs/reqs/workflow-orchestration/story.intent.json
scripts/run-single-activity grade_story_analysis docs/reqs/workflow-orchestration/story.analysis.json
scripts/run-single-activity --help
```

This starts a `SingleActivityWorkflow` (`single_activity_workflow.py`) that
schedules exactly the named Activity on the already-running
`orchestrator.worker`, then polls until it finishes and prints the result.
`repair_story_analysis` isn't supported (it needs two input files: the
analysis and its grade). On failure it points you at the Cadence Web UI
(`http://localhost:8088`) and `scripts/.run/worker.log` for the activity
task's history and the worker's own error output.

## Running the unit tests

```bash
nix-shell --run ".venv/bin/python -m pytest src/orchestrator -v"
```

All logic except the thin Cadence adapter (`workflow.py`'s `execute_activity`
calls and the `wait_condition`/`sleep` race) is covered by these tests. The
adapter itself is exercised manually via the steps above; a smoke test against a
real Cadence server is intentionally not part of the automated suite since it
requires the running Docker stack from `docker/docker-compose.yml`.
