# Hook event reference

Each event fires at a specific point in the agent lifecycle. The `matcher` field (a regex against `tool_name`) filters which tool invocations trigger a hook.

## Events

### PreToolUse

Fires before a tool executes.

- **Use:** block, modify, or add context to a tool call.
- **Stdin:** `tool_name`, `tool_input`.
- **Output:** `decision` / `reason`, or `hookSpecificOutput.updatedInput` to rewrite arguments.

### PostToolUse

Fires after a tool finishes executing.

- **Use:** logging, validation, follow-up actions.
- **Stdin:** `tool_name`, `tool_input`, `tool_response` (`success`, `output`, `error`).
- **Output:** `hookSpecificOutput.additionalContext` to inject text.

### PermissionRequest

Fires when the agent needs a permission decision.

- **Use:** custom approval logic.
- **Stdin:** `tool_name`, `tool_input`.
- **Output:** `{ "decision": "approve" | "block", "reason": "..." }`.

### UserPromptSubmit

Fires when the user submits a message.

- **Use:** add context or trigger workflows.
- **Stdin:** `prompt`.
- **Output:** `hookSpecificOutput.additionalContext` to inject a system message.

### Stop

Fires when the agent decides to stop.

- **Use:** prevent premature stopping or add follow-up instructions.
- **Stdin:** `stop_hook_active`.
- **Output:** `decision` / `reason` to block the stop.

### PostCompaction

Fires after context compaction completes successfully.

- **Use:** re-inject context that may have been lost, or log compaction.
- **Stdin:** `summary`.
- **Output:** `hookSpecificOutput.additionalContext`.

### SessionStart

Fires when a new session begins.

- **Use:** initialization, logging, environment setup.
- **Stdin:** `source`.
- **Output:** `hookSpecificOutput.additionalContext`.

### SessionEnd

Fires when a session ends.

- **Use:** cleanup or final logging.
- **Stdin:** `reason`.

## Matcher

The `matcher` is a regex applied to `tool_name` for tool events: `PreToolUse`, `PostToolUse`, `PermissionRequest`.

For non-tool events (`UserPromptSubmit`, `Stop`, `PostCompaction`, `SessionStart`, `SessionEnd`), use an empty string or omit `matcher`.

Common `tool_name` values:

- `exec`
- `edit`
- `read`
- MCP tools are formatted as `mcp__<server>__<tool>`.

## Output fields

| Field | Description |
|-------|-------------|
| `decision` | `approve` or `block`. |
| `reason` | Explanation shown to the agent. |
| `hookSpecificOutput.hookEventName` | Event this output targets. |
| `hookSpecificOutput.additionalContext` | Text injected into agent context. |
| `hookSpecificOutput.updatedInput` | Object merged into the tool call arguments for `PreToolUse`. |

## Exit codes

| Code | Meaning |
|------|---------|
| 0 | Success. |
| 2 | Block. |
| Other | Error, logged but not blocking. |
