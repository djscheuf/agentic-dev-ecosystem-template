# Activity Contracts for the Story Analysis Workflow

Each SDLC skill in the Story Analysis Workflow is wrapped by a thin Cadence Activity that shells out to the `devin` CLI in single-turn mode. The Activity does not reimplement the skill; it only adapts the skill's file-based contract (ADR-004) to a typed Cadence Activity result.

## Uniform Activity Interface

### Input: `SkillActivityInput`

| Field | Type | Description |
|---|---|---|
| `skill_name` | `string` | One of: `extract-story-intent`, `analyze-story`, `grade-story-analysis`, `repair-story-analysis`. |
| `input_paths` | `string[]` | Paths to the input JSON documents, relative to repo root. |
| `context` | `string` (optional) | Extra context passed straight through to the skill prompt, e.g. the original story path. |

### Output: `SkillActivityOutput`

| Field | Type | Description |
|---|---|---|
| `output_path` | `string` | Path to the JSON file the skill produced, relative to repo root. |
| `sentinel_path` | `string` | Path to the `.process/{skill}.done.json` sentinel written by the skill. |
| `status` | `"success" \| "failure"` | Whether the Activity wrapper considers the run successful. |

A `status` of `"failure"` (missing output, missing sentinel, or non-zero `verify.sh` exit) is raised as an `ActivityFailure` so Cadence's `RetryPolicy` applies.

## Per-Skill Contracts

### `extract-story-intent`

| Item | Value |
|---|---|
| Skill input | The story document or verbatim text. `input_paths[0]` is the story path; `context` may carry the same text. |
| Skill output schema | `.devin/skills/extract-story-intent/schema/story-intent.schema.json` |
| Output file | Same directory as the story document, named `{verb}-{object}-{context}.intent.json`. |
| Sentinel | `.process/extract-story-intent.done.json` with `verify_params.extracted_intent_path` and `verify_params.reference_document`. |
| Activity output `output_path` | The extracted intent JSON path. |
| Used by next step | `analyze-story` reads the intent JSON. |

### `analyze-story`

| Item | Value |
|---|---|
| Skill input | The extracted intent JSON from `extract-story-intent`. `input_paths[0]` is the intent path. |
| Skill output schema | `.devin/skills/analyze-story/schema/analysis.schema.json` |
| Output file | Same directory as the intent, named `{name}.analysis.json`. |
| Sentinel | `.process/analyze-story.done.json` with `verify_params.analysis_path`. |
| Activity output `output_path` | The analysis JSON path. |
| Used by next step | `grade-story-analysis` reads the analysis JSON. |

### `grade-story-analysis`

| Item | Value |
|---|---|
| Skill input | The analysis JSON. `input_paths[0]` is the analysis path. |
| Skill output schema | `.devin/skills/grade-story-analysis/schema/analysis-grade.schema.json` |
| Output file | Same directory as the analysis, named `{name}.analysis-grade.json`. |
| Sentinel | `.process/grade-story-analysis.done.json` with `verify_params.analysis_grade_path`. |
| Activity output `output_path` | The analysis-grade JSON path. |
| Used by next step | Workflow inspects the grade. If the score is below the pass threshold, `repair-story-analysis` is invoked. |

### `repair-story-analysis`

| Item | Value |
|---|---|
| Skill input | The current analysis JSON plus the full grader feedback. `input_paths` is `[analysis.json, analysis-grade.json]`. |
| Skill output schema | `.devin/skills/repair-story-analysis/schema/analysis.schema.json` (same shape as `analyze-story` output). |
| Output file | Overwrites the input analysis JSON. The grade file is not modified. |
| Sentinel | `.process/repair-story-analysis.done.json` with `verify_params.analysis_path`. |
| Activity output `output_path` | The repaired analysis JSON path (same as the input analysis path). |
| Used by next step | The Workflow re-runs `grade-story-analysis` against the repaired analysis. |

## Workflow Input Contract

The Workflow is started with a single `WorkflowInput` object:

```json
{
  "story_document": "docs/reqs/workflow-orchestration/story.md",
  "config": {
    "domain": "story-analysis-domain",
    "task_list": "story-analysis-tasklist",
    "cadence_target": "localhost:7833"
  }
}
```

- `story_document`: repo-relative path or verbatim story text.
- `config`: matches `domain-task-list-retry-config.json`.

## Activity Implementation Notes

- The Activity runs `devin -p --permission-mode auto --model SWE-1.6 -- ...` via `spawnSync` or `subprocess.run`, mirroring `evals/devin.js`.
- The skill writes its output and sentinel to disk; the Activity then reads the sentinel and checks the output file exists.
- Any non-zero exit from the `devin` subprocess, missing output, or failed `verify.sh` result raises an `ActivityFailure`.
- Activity durations are sized for LLM-agent runtime, not typical fast RPCs. See `domain-task-list-retry-config.json` for timeout/retry values.
