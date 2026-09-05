# Hooks

Hooks run custom logic at specific points in the agent lifecycle. They are supported by Devin Local and Devin CLI, and are not loaded in Restricted Mode.

## What hooks can do

- Enforce policies (block or allow actions).
- Add context to the agent's prompt.
- Run side effects (logging, notifications).
- Modify permissions or tool inputs.

## Hook file locations

| Location | Format | Notes |
|----------|--------|-------|
| `.devin/hooks.v1.json` | Hook object is the whole file | Recommended for new projects. |
| `.devin/config.json` | `"hooks"` key | Shared with team. |
| `.devin/config.local.json` | `"hooks"` key | Gitignored personal overrides. |
| `~/.config/devin/config.json` | `"hooks"` key | User-wide. |
| `.claude/settings.json` / `.claude/settings.local.json` | `"hooks"` key | Read when `read_config_from.claude` is true. |
| `~/.claude.json` / `~/.claude/settings.json` | `"hooks"` key | User-level Claude Code config. |

In `.devin/hooks.v1.json`, the top-level object contains the event names. In other files, hooks are nested under a `"hooks"` key.

## Hook format

Each entry under an event is an object with an optional `matcher` and an array of `hooks`.

```json
{
  "PreToolUse": [
    {
      "matcher": "exec",
      "hooks": [
        {
          "type": "command",
          "command": "./scripts/validate.sh",
          "timeout": 10
        }
      ]
    }
  ]
}
```

| Field | Description |
|-------|-------------|
| `matcher` | Regex matched against `tool_name`. Empty or omitted matches all tools. Only for tool events. |
| `type` | `"command"` to run a shell command, or `"prompt"` to evaluate an LLM prompt. |
| `command` | Shell command for `command` hooks. |
| `prompt` | Prompt text for `prompt` hooks. |
| `timeout` | Optional timeout in seconds. |

## Command hook input

Event data is passed as JSON on stdin. Example for `PreToolUse`:

```json
{
  "hook_event_name": "PreToolUse",
  "tool_name": "exec",
  "tool_input": { "command": "rm -rf /", "shell_id": "main" }
}
```

The `DEVIN_PROJECT_DIR` environment variable is set to the project root.

## Command hook output

A hook can print a JSON object to stdout to control the outcome.

### Block or approve

```json
{ "decision": "block", "reason": "Destructive command blocked by policy" }
```

### Inject context

```json
{
  "hookSpecificOutput": {
    "hookEventName": "UserPromptSubmit",
    "additionalContext": "Deploys require an approved change ticket."
  }
}
```

### Rewrite tool input (PreToolUse only)

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "updatedInput": { "command": "rtk git status" }
  }
}
```

Fields in `updatedInput` are merged into the tool call arguments.

## Exit codes

| Code | Meaning |
|------|---------|
| 0 | Success. Hook continues. |
| 2 | Block. Action is denied. |
| Other | Error. Logged but does not block. |

## Verify loaded hooks

Use the `/hooks` slash command in Devin Local or Devin CLI to list currently loaded hooks and their source files.
