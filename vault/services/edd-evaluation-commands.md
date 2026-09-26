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
