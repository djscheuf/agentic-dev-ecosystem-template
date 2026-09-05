# NixOS development environment

This repository is developed on NixOS. Use `nix-shell` as the default way to provide missing terminal or command-line dependencies.

*Last confirmed: 2026-08-29.*

## Current environment

- OS: NixOS 25.11 (Xantusia)
- `nix-shell`: 2.31.3 at `/run/current-system/sw/bin/nix-shell`

## Implications for agents

- Prefer `nix-shell` over `apt`, `brew`, `npm -g`, or manual downloads when a command-line tool is missing.
- Check whether a tool is already available in `/run/current-system/sw/bin` before entering a new shell.
- The project Devin configuration already allows `Exec(nix-shell)`, so agents can invoke it without a permission prompt.

## Test suite entry points (2026-09-02)

- `scripts/run_unit_tests.sh` runs isolated tests under `tests/unit`, `src/orchestrator/tests`, and `src/story_analysis_workflow/tests`.
- `scripts/run_integration_tests.sh` runs only `tests/integration` and requires Cadence on `localhost:7833`.
- `scripts/run_e2e_tests.sh` runs only `tests/e2e` and requires the Cadence server and Web UI.
- All three enter `nix-shell`, use `.venv/bin/python`, and forward additional pytest arguments.

## JSON Schema validation utility (2026-09-04)

- `.devin/skills/validate-json-schema/scripts/validate-json-schema.sh <schema.json> <document.json>` validates JSON with `python313Packages.jsonschema` supplied by `nix-shell`.
- The script prints concise validation errors and exits nonzero on invalid schemas or documents; no arguments or `--help` prints usage.
