# Debugging: Activity Failures

When an activity raises, the workflow's history gets an `ActivityTaskFailed` event with error
details. The error falls into one of four categories:

## Panic errors

**Cause:** a bug in the activity code — nil pointer dereference, out-of-range index, etc. Should
never be an *expected* outcome.

**Fix:** read the stack trace in the error details (via `cadence workflow show` or the Web UI) to
locate exactly where the panic occurred, then fix the root cause in the activity implementation.

## Custom errors

**Cause:** the activity intentionally returned `cadence.NewCustomError(reason, details)` (Go) or
raised a structured error with a reason (Python) — this is an *expected* failure mode the activity
author designed for.

**Fix:** this isn't really a bug — it's app-level error signaling. Handle it in the calling workflow
by branching on the error reason. See
[../02-go-client/error-handling-and-retries.md](../02-go-client/error-handling-and-retries.md) /
[../03-python-client/retries-and-error-handling.md](../03-python-client/retries-and-error-handling.md).

## Generic errors

**Cause:** an error Cadence doesn't recognize as a specific category — typically bubbling up from a
downstream dependency the activity calls (a failed HTTP request, DB error, etc.) via
`errors.New()`/`fmt.Errorf()` (Go) or a plain exception (Python).

**Fix:** this is application-specific and unexpected by definition — dig into the activity's
downstream dependencies to find the actual root cause. Consider converting known failure modes into
custom errors so the workflow can handle them explicitly instead of falling into this bucket.

## Blob size limit errors

**Cause:** a payload exceeded the server's configured max blob size. This applies to (non-exhaustive):

- Signal input
- Workflow input/output
- Workflow continue-as-new input
- Activity input/output
- Workflow/activity error details
- Record marker
- Heartbeat details

Limits are dynamically configured per domain (see the server's dynamic config).

**Fix:** don't pass large payloads through Cadence directly. Store the data in external storage (S3,
a database, a blob store) and pass a **reference** (key/URL/ID) through the workflow/activity
instead. This is also good practice independent of hitting the limit — see
[../02-go-client/activities.md](../02-go-client/activities.md) on keeping activity payloads small,
since large payloads bloat every replay's Event History transfer regardless of the hard limit.

## Diagnostic flow

1. `cadence workflow show -w <id>` — find the `ActivityTaskFailed` event and read its `reason` /
   `details`.
2. Classify: panic (fix code) / custom (expected, handle in workflow) / generic (investigate
   downstream dependency) / blob-size (move data out-of-band).
3. If it's a downstream dependency issue, check that service's own logs/metrics — Cadence has no
   visibility into *why* the downstream call failed, only that the activity returned an error.
