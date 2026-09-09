---
name: utility-script-writing
description: "Use this skill whenever creating or substantially modifying a utility script, command-line script, maintenance script, migration helper, batch processor, automation script, or other executable tool. Require discoverable help and a safe dry-run mode so future users can understand and verify behavior before making changes."
---

# Utility Script Writing

## Purpose

Create utility scripts that are understandable, previewable, and safe for future users to operate without reading the implementation first.

Use this skill when writing or substantially modifying scripts that scan, copy, move, rename, delete, transform, publish, migrate, or otherwise process files or external state. Apply the same defaults to scripts in any language.

## Required defaults

Every utility script must provide both:

1. A help flag.
2. A dry-run flag.

Do not omit these defaults merely because the script is currently small, intended for one-time use, or expected to have only one user.

## Help flag

Provide conventional `-h` and `--help` flags unless the language or CLI framework has a stronger established convention.

Help output must explain:

- What the utility does.
- What inputs it reads.
- What state it may create, modify, move, or delete.
- Default source and destination locations, when applicable.
- Every argument and option.
- Skip, overwrite, conflict, and error behavior.
- At least one normal example.
- A dry-run example.
- Clear warnings for destructive options.

Prefer the language's standard argument-parsing library so help formatting and invalid-argument handling are consistent. For Python, prefer `argparse` unless the repository already standardizes on another CLI framework.

## Dry-run flag

Provide a `--dry-run` flag for any utility capable of side effects.

When enabled, dry-run mode must:

- Perform the same discovery, filtering, validation, naming, and conflict checks as a real run whenever practical.
- Report what would be created, copied, modified, moved, renamed, deleted, uploaded, or otherwise changed.
- Produce a summary with useful counts.
- Make no persistent changes.
- Avoid creating destination directories, temporary files, caches, lock files, or other artifacts unless strictly necessary for safe analysis.
- Never invoke destructive operations.
- Exit nonzero when the corresponding real run would be blocked by invalid input or unresolved errors.

Use explicit prospective wording such as `would copy`, `would update`, and `would delete`. Do not label an operation as completed during a dry run.

## Side-effect design

Structure the implementation so discovery and planning are separate from execution. Prefer this flow:

1. Parse and validate arguments.
2. Discover candidate inputs.
3. Build a deterministic operation plan.
4. Report the plan.
5. Stop when `--dry-run` is enabled.
6. Execute the plan.
7. Report completed operations and totals.

For destructive behavior:

- Require an explicit option in addition to the absence of `--dry-run`.
- Complete and verify prerequisite copy, backup, or transformation operations before deleting sources.
- Include already-satisfied or skipped prerequisites only when the script's documented policy makes them safe.
- Deduplicate destructive targets.
- Prevent deletion of source roots, destination roots, or paths outside the intended boundary.
- Make destructive targets conspicuous in both detailed output and summaries.

## Verification checklist

Before considering a utility script complete, verify:

- `-h` and `--help` exit successfully and accurately describe current behavior.
- `--dry-run` exercises representative discovery and validation paths.
- Dry-run leaves the filesystem or external system unchanged.
- Normal execution performs the planned operation.
- Existing-target behavior is tested.
- Destructive behavior is tested only against temporary or disposable fixtures.
- Paths containing spaces and Unicode characters are handled when relevant.
- Output distinguishes planned, completed, skipped, and failed operations.
- The summary counts agree with detailed output.

Never test a destructive option against real user data unless the user explicitly asks to execute that specific destructive operation after reviewing the plan.
