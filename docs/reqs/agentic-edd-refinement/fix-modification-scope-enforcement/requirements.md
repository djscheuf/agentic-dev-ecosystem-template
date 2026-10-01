# Fix Modification-Scope Enforcement in EDD Refinement — Requirements & Analysis

## Bottom line

A recent `kickoff-edd-refinement.sh` run against `docs/reqs/refine-grade-design/edd_input.json`
had its `edd-do` step modify files inside `src/edd_refinement_workflow` — the workflow's own
source — instead of staying within the target skill's authorized scope
(`.devin/skills/grade-story-design/SKILL.md`, `.devin/skills/grade-story-design/rubric.md`).
The workflow did not stop the run in an alarmed way when this happened.

Root cause analysis (this document) found that `modification_scope`, the field in the portable
`edd_input.json` document that is supposed to be the single source of truth for what a run is
allowed to touch, is used **once**, at preflight, purely to check that the listed paths resolve
inside the repo. It is then discarded. Nothing downstream — not `edd-plan`, not `edd-do`, not
`validate_candidate` — ever checks a proposed or actual change against it. The only scope check
that exists today (`validate_candidate`'s `out_of_scope` reason) compares the real diff against
`intended_files`, which is self-reported by the `edd-plan` skill itself, not against the run's
authorized scope. And even when that self-report check *does* fire, the workflow's response is a
quiet `return` — no revert, no `finalize_run`, no distinguishable failure signal.

This document scopes the fix: (1) persist and enforce the *authorized* `modification_scope`
(directories and/or explicit files) at both Plan time and Do time, and (2) turn a confirmed
out-of-scope modification into a hard, alarmed stop instead of a silent one.

See also:
- [[vault/services/edd_refinement.md]] — current implementation status log.
- [[vault/decisions/ADR-017-agentic-edd-quality-ratchet.md]], [[ADR-023-persistent-process-safe-mutation-lease.md]].
- `docs/reqs/agentic-edd-refinement/fix-edd-workflow/requirements.md` — prior repair of the same workflow (edd-plan/edd-do skill wiring); this document does not revisit that work.

## Confirmed gaps

| # | Gap | Where | Evidence |
|---|---|---|---|
| 1 | `modification_scope` is validated for existence/containment at preflight, then dropped. It never reaches `progress.json`, `refinement.yaml`'s per-iteration context, `edd-plan`, or `validate_candidate`. | `cli.py:83-95` → `common/preflight.py:71-79` | `resolve_and_validate_target_repository`'s `scoped_paths` param is only used inside the `if scoped_paths:` block; the resolved list is never returned or attached to `PreflightResult`. `initialize_run.py`'s `record` dict has no `modification_scope` key. |
| 2 | The only live scope check (`validate_candidate`'s `out_of_scope` reason) compares the actual diff to `intended_files` — the `edd-plan` skill's own self-reported claim about what it plans to touch — never to the run's authorized `modification_scope`. A plan that (incorrectly, or through prompt-injection-style drift) proposes `intended_files` outside the authorized scope would pass this check as long as `edd-do`'s diff matches its own plan. | `activities/validate_candidate.py:47-66`, `activities/edd_plan.py:195-210` | `intended_files=plan.get("intended_files")` — no comparison to `modification_scope` anywhere in `edd_plan.py`. |
| 3 | When `validate_candidate` does return `status != "scope_valid"` (including `out_of_scope`), `workflow.py` does `result.update(...); return result` and exits the loop with no further action. | `workflow.py:229-232` | No call to `finalize_run`, no repository revert, no distinct terminal reason. Cadence records this as a normal successful workflow completion, not a failure. Confirmed via `test_workflow.py`: `test_candidate_status_query_returns_current_candidate` only asserts the query surface for an `out_of_scope` candidate dict — no test exercises `workflow.run()` end-to-end for this status to check `finalize_run` is invoked. |
| 4 | `FinalizeRunActivity.run` only restores the worktree (`git reset --hard <commit>`) when `best_accepted_state` is present. If a run ends (for any reason, including a scope violation) before any candidate has ever been accepted, the worktree is never reset — an out-of-scope or otherwise stray uncommitted diff is left sitting in the repo indefinitely. | `finalize_run.py:27-33` | `if accepted_commit is not None: self.restore(accepted_commit)` — no `else` branch resetting to `starting_revision`. |
| 5 | The mutation lease (ADR-023) is only guaranteed to be released on a normal `finalize_run` call or an *unhandled exception* escaping `EddRefinementWorkflow.run`. The current quiet `return` in gap #3 is neither, so the lease is held until TTL expiry even though the run is effectively dead. | `workflow.py:24-44` (exception-driven finalize), `finalize_run.py:33` | ADR-023 documents the exception-driven finalize path but that path is never entered by the out-of-scope return. |

Net effect: an out-of-scope write can go completely undetected (gap 2), and even when it *is*
detected, the run doesn't fail loudly, doesn't clean up after itself, and doesn't release its
lease promptly (gaps 3-5).

## What already works and should be reused as-is

| Concern | File(s) | Keep? |
|---|---|---|
| Real git-diff-based change detection (`execution.changed_files`, `diff_hash`) | `activities/edd_do.py:74-104` | Yes — ground truth for "what actually changed," independent of what any skill claims. This is what the new `modification_scope` check should be layered onto. |
| `intended_files` vs. actual-diff comparison mechanics | `activities/validate_candidate.py:47-66` | Yes — keep as a *first* check (catches `edd-do` drifting from its own plan); add the `modification_scope` check alongside it, not instead of it. |
| `ScopedPathValidator` path-containment logic | `common/scoped_path_validator.py` | Yes, as the base primitive — but it currently only asks "is X inside the repo root," not "is X inside one of these specific allowed paths." Needs a sibling/extension for scope-list membership (see Requirement 2 below). |
| Exception-driven finalize-on-exit safety net | `workflow.py:24-44` (ADR-023) | Yes — the cleanest way to make an out-of-scope detection into a hard stop is to raise into this existing path, not build a second finalize-on-error mechanism. |
| `refinement.yaml`'s embedded `edd_input` (already includes raw `modification_scope` strings) | `activities/initialize_run.py:97-125` | Yes, as the historical record — but this is documentation-only context for a human/agent reading the file later, not a machine-enforced value. The enforcement path (Requirement 1) is separate and must not rely on an agent reading this doc correctly at Plan time only. |

## Requirements

### 1. Persist the authorized `modification_scope` for the life of the run

- At `initialize_run`, resolve `modification_scope` from the input document to a list of
  **repo-relative, POSIX-style path entries** (mirroring how `changed_files` is reported by
  `git diff --name-only`) and store it in the progress record (e.g. `record["modification_scope"]`).
- Each entry may name either:
  - an exact file (e.g. `.devin/skills/grade-story-design/rubric.md`), or
  - a directory prefix, meaning everything nested under it is authorized (e.g.
    `.devin/skills/grade-story-design/_tests/`).
- Thread this persisted value into every activity that needs to check a file against it
  (`edd_plan`, `validate_candidate`) the same way `iteration_start_baseline` is already threaded
  per the pattern in `vault/services/edd_refinement.md`'s "`iteration_start_baseline` threading"
  section — read from the progress record, not re-derived or re-passed from the original CLI
  input, so resumed runs behave identically to fresh ones.
- Add `modification_scope` to `ProgressRecordSerializer.for_v5`'s `allowed_fields` (currently
  unused on the save path per the vault's note on `iteration_start_baseline`, but keep the two
  consistent so a future round-trip path doesn't silently drop one and not the other).

### 2. Path-containment check supporting both files and folders

- Add a shared helper (e.g. `common/scoped_path_validator.py::PathScopeChecker` or similar) that,
  given a repo-relative candidate path and the authorized `modification_scope` list, returns
  whether the candidate is authorized:
  - exact string match against a scope entry, OR
  - the candidate's path is nested under a scope entry treated as a directory prefix (use
    `PurePosixPath.is_relative_to`-equivalent logic, not naive string prefixing, to avoid
    `foo-bar/x` incorrectly matching a scope entry of `foo`).
- This helper is the single place both `edd-plan`'s pre-check (Requirement 3) and
  `validate_candidate`'s hard check (Requirement 4) call into, so the containment semantics can
  never drift between the two call sites.

### 3. Optional pre-check at `edd_plan` time (fail before `edd_do` ever runs)

- After `EddPlanRunner` reads the skill's `plan.json`, check every entry in `plan["intended_files"]`
  against the persisted `modification_scope` using the Requirement 2 helper.
- If any `intended_files` entry is out of scope:
  - do **not** invoke `edd_do`,
  - capture enough of the plan's own reasoning to diagnose *why* it proposed an out-of-scope
    change — at minimum `action`, `rationale`, `evidence`, and the offending `intended_files`
    entries — into both the returned `PlanningResult` and the run's durable record (see
    Requirement 5's capture format; this is the same payload shape, just triggered earlier in the
    loop).
  - route to the same hard-stop handling as Requirement 4 (this is a "detected at plan time"
    variant of the same failure, not a different one).

### 4. Hard check at `validate_candidate` time (ground truth against the real diff)

- In addition to the existing `intended_files`-vs-`changed_files` check, add a second,
  independent check: every entry in `execution.changed_files` must be authorized per the
  persisted `modification_scope` (Requirement 2 helper), regardless of what `intended_files`
  claimed.
- This is the check that would have caught the reported incident: `edd-do` diverging from its own
  plan and writing into `src/edd_refinement_workflow`, which is outside `modification_scope`
  regardless of what `intended_files` said.
- Keep both checks distinguishable in the result (e.g. `rejection_reason` values
  `plan_out_of_scope` vs. `diff_out_of_scope`, or a shared `out_of_scope` reason plus a detail
  field naming which check failed and which path(s) triggered it) so the terminal report and any
  human reviewing it can tell "the plan asked for something out of bounds" apart from "the agent
  did something the plan didn't even mention."

### 5. Promote a confirmed out-of-scope result to a hard, alarmed stop

An out-of-scope detection (from either Requirement 3 or Requirement 4) must become a rejection
reason that **halts the run before proceeding**, not a status that gets recorded and then the run
quietly ends. Concretely:

- `workflow.py` must branch on the out-of-scope rejection reason specifically (distinct from
  benign rejection reasons like `no_op` or `ambiguous_test_change`, which are legitimate
  "try again next iteration" outcomes and must keep their current behavior).
- On out-of-scope:
  - revert any uncommitted worktree changes the offending attempt produced (only relevant for the
    Requirement 4 / post-`edd_do` case — there is nothing to revert for the Requirement 3 /
    pre-`edd_do` case),
  - capture the diagnostic payload (offending action, rationale, evidence, offending path(s), and
    which check caught it) into the run's durable record / terminal report, so a human can see
    *why* the agent thought it needed to touch an out-of-bounds file,
  - raise a dedicated exception (e.g. `OutOfScopeModificationError`) from within `_run`, reusing
    the existing exception-driven finalize path in `EddRefinementWorkflow.run` (ADR-023) rather
    than adding a second, parallel finalize-and-release code path. This guarantees the lease is
    released and a terminal report is written even if a future change to `_run` forgets to call
    `finalize_run` explicitly on this branch.
  - `finalize_run`'s `terminal_reason` for this path must be a distinct, greppable value (e.g.
    `out_of_scope_modification`) so it is not confused with budget/regression stops in monitoring
    or in the terminal report.

### 6. `finalize_run` must always leave a clean worktree

- Fix `FinalizeRunActivity.run` to restore to `starting_revision` when there is no
  `best_accepted_state` (today it only restores when a candidate has been accepted), so any run
  that ends — for any terminal reason, including this one — never leaves stray uncommitted changes
  in the target repository.

## Non-goals

- **Preventing** `edd-do` (the agentic skill) from attempting an out-of-scope write in the first
  place. The skill's own `SKILL.md` "Verify Scope" step (Step 5) is a prompt-level self-check and
  stays as defense-in-depth, but it is not trustworthy as the sole control — this document is
  entirely about the deterministic detection/kill layer *outside* the skill, per the user's
  framing ("less worried about preventing edd-do from changing files, and more about detecting an
  out-of-bounds modification and killing the workflow when we see it go off the rails").
- Sandboxing or OS-level filesystem restrictions on the harness process.
- Changing the authorized-action taxonomy (`add_coverage`, `repair`, `refine_skill`,
  `refine_supporting_docs`, `propose_evaluation_expectation_change`, `stop`) — this is purely
  about *where* a change is allowed to land, not *what kind* of change is allowed.

## Open questions

1. Should a confirmed out-of-scope stop count toward `consecutive_confirmed_regressions` or any
   existing budget counter, or is it always an immediate, separate terminal state regardless of
   remaining budget? (Leaning: always immediate/separate — an out-of-scope write is a control
   failure, not a quality regression, and conflating the two would let 1-2 tolerated "regressions"
   mask a scope breach.)
2. Do we want a dedicated `scope_violations` list in the progress record / terminal report
   (parallel to `regression_evidence`) for observability across runs, or is a single terminal
   report entry sufficient given a scope violation always ends the run?
3. For the Requirement 3 pre-check: should a plan-time scope violation still get recorded as a
   `candidate` (with a rejection reason) for `get_candidate_status()` symmetry with the
   post-`edd_do` case, even though no `edd_do`/`validate_candidate` activity ever ran? Affects
   whether external pollers watching `get_candidate_status` see a consistent shape regardless of
   which check caught the violation.
4. Directory scope entries: should trailing-slash normalization be enforced at `EddRefinementInput.from_path`
   parse time (input.py), or handled defensively wherever the containment check runs? Leaning
   toward normalizing once at parse time so every downstream consumer sees a canonical form.
