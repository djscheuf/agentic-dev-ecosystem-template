# EDD Evaluation Run/Inspect Commands

The `test_command` in an EDD refinement input must invoke `scripts/run-eval.js` directly; do not route it through `npm run test`, because npm's lifecycle banner pollutes stdout and breaks the JSON identity contract.

## Identity-chain contract

1. The workflow runs `test_command` in the repository root.
2. `test_command` must print exactly one JSON line to stdout:
   ```json
   {"evaluation_id": "eval-<id>"}
   ```
3. The workflow substitutes that id into `inspect_command` wherever `{evaluation_id}` appears.
4. `inspect_command` returns the raw list of per-result objects used to compute pass/fail/coverage metrics.

See [[decisions/ADR-021-edd-evaluation-command-contracts.md]] for why non-zero exits are normal results and [[decisions/ADR-022-edd-evaluation-command-artifacts.md]] for raw command capture.

## Why `npm run test` breaks the contract

`npm run test <config>` prints a banner like this to stdout:

```text

> test
> node scripts/run-eval.js $1 <config>

{"evaluation_id":"eval-abc-2026-01-01T00:00:00"}
```

The Python harness tries to parse the *entire* stdout as JSON, fails, and returns `{}`. `extract_evaluation_id` then raises:

```
evaluation result missing evaluation_id: []
```

`npm run test --silent` avoids the banner, but the positional `$1` handling in `package.json` is also fragile across npm versions. Calling the Node script directly removes both failure modes.

## Recommended command shape

In an EDD input JSON:

```json
"test_command": [
    "node",
    "scripts/run-eval.js",
    "gradeDesign.tests.yaml"
]
```

Manual dry-run:

```bash
node scripts/run-eval.js --dry-run gradeDesign.tests.yaml
```

## Extra promptfoo flags

`run-eval.js` forwards any additional arguments to `promptfoo eval` after `--config <file>`:

```bash
node scripts/run-eval.js gradeDesign.tests.yaml --filter-pattern "TC-001.*"
```

## Inspect command shape

Use `{evaluation_id}` as a placeholder so the workflow substitutes the exact id:

```json
"inspect_command": [
    "node",
    "scripts/inspect-eval.js",
    "{evaluation_id}",
    "--all",
    "--json"
]
```

This must continue to return a JSON array of per-result objects (or a dict with `passing/failing/total/percentage`) so the harness can compute metrics and coverage.

## Compact inspection for agents / humans

`scripts/inspect-eval.js` also supports `--compact-json`, which produces a small, agent-friendly summary that includes *all* test cases:

```bash
node scripts/inspect-eval.js eval-<id> --compact-json
```

Output:

```json
{
  "passing": 22,
  "failing": 1,
  "total": 23,
  "percentage": 95.65,
  "tests": [
    { "index": 0, "description": "TC-001 ...", "status": "pass", "provider": "...", "metadata": {...} },
    { "index": 5, "description": "TC-006 ...", "status": "fail", "provider": "...", "metadata": {...},
      "vars": {...}, "prompt": "...", "output": "...", "gradingResult": {...} }
  ]
}
```

Passing cases include only identification fields; failing cases include the rendered prompt, variables, raw output, and failed assertion details. Unlike `--json`, `--compact-json` defaults to showing every test because the passing entries are already minimal.

### Preserving coverage computation

If the EDD harness needs to compute required-test-case coverage, pass `--coverage-metadata-property <path>` so the compact JSON still mirrors the aggregated coverage metadata at the top level:

```bash
node scripts/inspect-eval.js eval-<id> --compact-json --coverage-metadata-property metadata.covers_test_case_ids
```

This collects the specified metadata field from every test case and places it at the same dotted path in the output, keeping the `CoverageCalculator` contract intact.
