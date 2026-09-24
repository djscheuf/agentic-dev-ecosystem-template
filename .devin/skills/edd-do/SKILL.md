---
name: edd-do
description: Implements the single refinement action selected by edd-plan against a target skill's prompt, supporting documents, or evaluation suite, strictly within the authorized file scope. Use immediately after edd-plan in each EDD refinement iteration.
---

# EDD-Do

## Purpose
Apply exactly one planned refinement action to a target skill and/or its evaluation suite. Make only the change described in the plan.

**No shell commands.** Do not run shell commands (`exec`, `git`, `npm`, etc.) — every needed check is either a file edit or a re-read. The workflow runs validation (scope checks, the full evaluation) deterministically after this skill completes.

## Prerequisites
- `iterations/<n>/plan.json` exists and names an authorized action, `intended_files`, and `expected_effect`.
- The target repository worktree has no stray edits from a previous, not-yet-committed-or-reverted attempt.
- If `action` is `propose_evaluation_expectation_change`, approval has already been recorded for this exact proposal. If it has not, STOP and report this to chat instead of proceeding — never apply an unapproved expectation change.

## Workflow Steps

### Step 1: Read the Plan
```
Read iterations/<n>/plan.json:
- action
- intended_files
- rationale
- expected_effect
- iteration_start_baseline

Read refinement.yaml's latest section for full narrative context and any
"changes made" notes left by a prior, related iteration.
```

### Step 2: Load Skill and Eval Context
```
Read the target skill's SKILL.md / prompt and any supporting documents
named in intended_files.

If the change touches promptfooconfig.yaml, test YAML, custom
assertion/transform JS, or fixtures:
  → Consult the `promptfoo` skill FIRST.
  → Use its phase map to jump to the specific section needed
  instead of guessing at syntax or option names.
```

### Step 3: Make the Minimal Change
```
Modify ONLY the files listed in intended_files.

By action type:

- refine_skill:
    Edit only the prompt/instruction sections implicated by the
    failure evidence in the plan. Do not rewrite unrelated sections.

- repair:
    Fix the fixture/assertion/helper defect without lowering the bar
    the evaluation is meant to enforce. Prefer fixing an internally
    inconsistent fixture over relaxing an assertion. If the true cause
    is a helper bug (e.g. `||` treating `0` as falsy), fix the helper,
    not the test data.

- add_coverage:
    Add the missing required test case(s). Prefer an existing,
    already-rich fixture over authoring a new one; follow the target
    skill's own fixture-naming and YAML-block conventions (copy an
    existing block, change only what differs).

- refine_supporting_docs:
    Edit only the referenced/example/template document(s) named in
    intended_files.

- propose_evaluation_expectation_change:
    Change only the approved expectation, exactly as approved. Adhere to the approved diff, other changes are forbidden

- Editing a file not listed in intended_files IS FORBIDDEN  
- Refactoring, renaming, or "improving" anything the plan did not ask for IS FORBIDDEN
- Weakening an expectation to make a failure disappear instead of
  fixing the underlying fixture, helper, or skill behavior IS FORBIDDEN
```

### Step 4: Re-read and Validate Every Edit
```
Do NOT run the promptfoo evaluation suite or any shell command here —
validation is a separate deterministic workflow step (check_candidate)
that runs after this skill completes.

Instead, re-read each file you edited and confirm by inspection:
- YAML files parse cleanly (indentation, anchors, block structure)
- JSON fixtures are valid (balanced braces, quoted keys, no trailing commas)
- Helper JS is syntactically consistent

Fix and re-check until every edited file reads cleanly.
```

### Step 5: Verify Scope
```
List every file you created or modified during this session and confirm
each appears in intended_files and in the run's overall authorized
modification_scope.

If anything else changed:
  → Revert the out-of-scope change before finishing.
  → If the out-of-scope change was necessary, STOP and report it to
    chat instead of silently expanding scope.
```

### Step 6: Document What Actually Changed
```
Append a "Changes made" subsection under the current iteration's
section in .process/edd/<run_id>/refinement.yaml:
- files touched
- one line per file describing the change
- how the actual change differs from the plan, if it does, and why
```

### Step 7: Write the Sentinel File
- Write the sentinel to the exact path given in the invocation prompt (e.g. `<plan-dir>/.process/edd-do.done.json`), creating the parent `.process/` directory when needed. The sentinel must not be removed after verification.
- the sentinel file will follow @/schema/sentinel.schema.json.
- set the task field to "edd-do".
- the verify_params of the sentinel file will follow @/schema/verify-params.schema.json.
- set the verify_params as follows:
    - set "plan_path" to the path of `iterations/<n>/plan.json`, relative to repo root.
    - set "iteration_number" to `<n>`.
    - set "action" to the action executed.
    - set "changed_files" to an array of every changed file, relative to repo root.

## Quality Checks
- [ ] Every changed file is listed in `intended_files`
- [ ] Made ONLY approved evaluation expectation changes
- [ ] Deterministic pre-run checks (YAML/JSON/JS syntax) pass
- [ ] `refinement.yaml` records what was actually changed, and any deviation from the plan
- [ ] The `promptfoo` skill was consulted for any eval-suite edit
