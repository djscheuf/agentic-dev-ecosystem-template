# ADR-010: Story Analysis WorkflowID Uses a Kickoff-Time Zettel ID, Not a Content Hash

**Date:** 2026-08-31
**Status:** Accepted

## Decision

`story_analysis_workflow.starter._default_workflow_id()` derives the default `WorkflowID` for a
`StoryAnalysisWorkflow` execution from the story document's name plus a "zettel id" — a
`YYYYMMDDHHmm` timestamp (24-hour, local to the caller) taken at kickoff time — instead of a
slug-of-input + SHA-256 content hash.

Format: `story-analysis-<name>_<YYYYMMDDHHmm>`. `<name>` is the file basename with its extension
stripped when the input looks like a path (e.g. `docs/example_story.md` -> `example_story`), or a
slug of the raw text otherwise. Example: kicking off `example_story.md` at 14:30 local time on
2026-08-31 produces `story-analysis-example_story_202608311430`.

## Rationale

The previous scheme (`story-analysis-<slug>-<sha256[:8]>`) made the `WorkflowID` a pure function of
the story content, so re-kicking off the exact same story file was rejected as a duplicate
(`WORKFLOW_ID_REUSE_POLICY_REJECT_DUPLICATE`) rather than starting a second, concurrent run. That
was a deliberate way of closing the "Concurrent workflow executions for the same story" edge case
(see `docs/reqs/workflow-orchestration/streams/client-api.stream.json`).

The user-facing need changed: operators want each `scripts/kickoff-analyze-story` invocation to be
independently addressable and orderable by *when* it ran, not collapsed into one run keyed by *what*
it analyzed. A timestamp-derived id makes each run's identity obvious from the id alone (useful in
the Cadence Web UI, logs, and when a story is intentionally re-analyzed after being edited).

## Trade-offs

**Advantage:** Human-readable, time-ordered `WorkflowID`s; re-running the same story (e.g. after
edits, or to retry) always starts a fresh execution without needing an explicit `--workflow-id`.

**Disadvantage:** Content-based dedup is gone. `RejectDuplicate` now only prevents two starts for
the *same story name in the same clock minute* — it no longer prevents two operators from
kicking off two runs of an unchanged story file five minutes apart. This was an explicit, accepted
tradeoff (not a regression to silently work around): the "Concurrent workflow executions for the
same story" edge case is now only closed at minute granularity, not at content granularity.
Callers who need strict dedup should pass an explicit `--workflow-id`/`workflow_id=`.

## Implementation

- `src/story_analysis_workflow/starter.py`: `_name_component()` extracts the path-basename (minus
  extension) or slugifies verbatim text; `_zettel_id()` formats `datetime.now()` (or an injected
  `when=` for tests) as `%Y%m%d%H%M`; `_default_workflow_id()` combines them.
- `src/story_analysis_workflow/tests/test_starter.py` covers: format of the generated id, and that
  `_default_workflow_id(..., when=...)` is deterministic for a fixed `when` but differs across
  different `when` values.

## Related Decisions

- None yet in this vault directly predate this; see `vault/services/cadence.md` for the broader
  Client API context this starter lives in.
