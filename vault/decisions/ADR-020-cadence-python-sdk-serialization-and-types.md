# ADR-020: Cadence Python SDK Serialization and Reconstruction Require JSON-Safe Types and Explicit Type Hints

**Status:** Accepted
**Date:** 2026-09-22
**Author:** @project-team

## Bottom line

The Cadence Python SDK serializes workflow/activity arguments with `msgspec.json` and reconstructs them on the worker using `inspect.get_type_hints`. Arguments must be JSON-serializable and the receiving function must declare the expected type, otherwise the worker receives an untyped dict and attribute access fails.

## Context

The agentic EDD workflow passes a `PreflightResult` dataclass from the CLI/client to the `EddRefinementWorkflow` and on to the `initialize_run` Activity. The dataclass contained a `pathlib.Path` (`repo_root`) field. The SDK encoder raised:

```
TypeError: Encoding objects of type PosixPath is unsupported
```

After converting `repo_root` to `str`, the client could start the workflow, but the Activity then failed with:

```
AttributeError: 'dict' object has no attribute 'target_context'
```

because the Activity parameter had no type hint, so the SDK did not convert the decoded dict back into the dataclass.

## Decision

- Keep all Cadence message payloads fully JSON-serializable: no `pathlib.Path`, no custom objects that `msgspec` cannot encode.
- Convert filesystem paths to `str` before they enter workflow/activity payloads and rehydrate them with `Path(...)` only where filesystem operations are needed.
- Add explicit type annotations to workflow `run` methods and activity entrypoints when the argument should be reconstructed into a dataclass.
- Treat missing type hints on Cadence entrypoints as a bug, because the default decode path returns a plain dict.

## Consequences

### Positive

- Workflow and Activity arguments round-trip correctly through the Cadence service.
- Type hints make the serialization contract visible and enforceable by the SDK.

### Negative

- Path fields become `str` in shared dataclasses, so every filesystem consumer must wrap them in `Path(...)`.
- Developers must remember to annotate new workflow/activity parameters; untyped params silently degrade to dicts.

### Neutral / Follow-up

- Consider a small lint or test that validates that dataclasses used in Cadence payloads contain only JSON-safe field types.
- Document this requirement in skill authoring guides if skills ever emit path-like values.

## Alternatives Considered

- **Custom `msgspec` enc_hook/dec_hook for `Path`** — rejected because it couples serialization to a platform-specific type and would not survive conversion to other Cadence SDKs (Go/Java).
- **Pass payloads as plain dicts everywhere** — rejected because it discards the structure and type safety already provided by the dataclass model.
