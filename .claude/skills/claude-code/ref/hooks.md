# Claude Code hooks

User-defined commands/HTTP endpoints/MCP tools/LLM prompts/agents that run automatically at lifecycle points. Deterministic control — fires regardless of what the model decides.
Source: https://code.claude.com/docs/en/hooks (reference) · https://code.claude.com/docs/en/hooks-guide (guide)

## Configuration shape

Defined under the `hooks` key in any settings.json (precedence applies; entries merge across levels — never replace). Also: plugin `hooks/hooks.json`, skill/subagent YAML frontmatter (skill hooks persist for rest of session; `once: true` removes after first success; subagent hooks live only while that agent runs, `Stop`→`SubagentStop`).

```json
{
  "hooks": {
    "<Event>": [
      {
        "matcher": "Bash|Edit",
        "hooks": [
          { "type": "command", "command": "...", "if": "Bash(git *)", "timeout": 60 }
        ]
      }
    ]
  }
}
```

Three levels: **event** → **matcher group** → **handler(s)**. All matching handlers run in parallel; same handler defined twice across files runs once.

## Events (lifecycle order)

Per session: `Setup` (via `--init`/`--maintenance`/`-init-only`), `SessionStart` (matchers: `startup|resume|clear|compact|fork`), `SessionEnd` (`clear|resume|logout|prompt_input_exit|other`).
Per turn: `UserPromptSubmit` (blockable — prompt never reaches Claude), `UserPromptExpansion` (typed /command expanded; blockable; matcher = command name), `Stop`, `StopFailure` (matcher = error type: `rate_limit|overloaded|authentication_failed|billing_error|invalid_request|model_not_found|server_error|max_output_tokens|cloud_credential_error|unknown`; output ignored).
Agentic loop: `PreToolUse`, `PermissionRequest`, `PermissionDenied` (auto-mode denials; `hookSpecificOutput.retry: true` lets model retry), `PostToolUse`, `PostToolUseFailure`, `PostToolBatch` (after parallel batch, before next model call — can stop loop), `SubagentStart`/`SubagentStop` (matcher = agent type), `TaskCreated`/`TaskCompleted`, `TeammateIdle`.
Context/lifecycle: `InstructionsLoaded` (matcher: `session_start|nested_traversal|path_glob_match|include|compact`), `ConfigChange` (`user_settings|project_settings|local_settings|policy_settings|skills`; blocks changes except policy), `CwdChanged`, `DirectoryAdded` (`slash_command|register_repo_root`), `FileChanged` (matcher = literal filenames to watch), `PreCompact`/`PostCompact` (`manual|auto`), `PreModelSwitch` (blockable) /`PostModelSwitch`, `Elicitation`/`ElicitationResult` (MCP input requests; matcher = server name), `Notification` (matcher = notification type, e.g. `permission_prompt`, `idle_prompt`, `agent_completed`), `WorktreeCreate`/`WorktreeRemove` (replaces gate behavior; any non-zero exit fails), `MessageDisplay` (display-only rewrite via `displayContent`).
No matcher support: `UserPromptSubmit`, `PostToolBatch`, `Stop`, `TeammateIdle`, `TaskCreated`, `TaskCompleted`, `WorktreeCreate/Remove`, `CwdChanged`, `MessageDisplay`.

## Matchers

- `""`, `"*"`, or omitted = match all
- Only `[A-Za-z0-9_\- ,|]` chars → exact string or list split on `|`/`,` (`Edit|Write`, `Edit, Write`)
- Any other char → unanchored JS regex (`mcp__memory__.*` matches all memory-server tools — the `.*` is REQUIRED; `mcp__memory` matches nothing)
- `if` field on a handler = one permission-rule filter on tool+args (`"Bash(git *)"`, `"Edit(**/*.ts)"`); tool events only; `$()`/backtick/unknown expansions cause the hook to run anyway (best-effort — use `permissions.deny` for hard enforcement). One rule per `if`; no `&&`/`||`.

## Handler types & fields

Common: `type` (required), `if`, `timeout` (sec; defaults 600 command/http/mcp_tool, 30 prompt, 60 agent; SessionEnd shares ~1.5s budget), `statusMessage`, `once` (skills only).

- `command`: `command` + optional `args` (present → **exec form**: direct spawn, no shell, placeholders safe unquoted; absent → **shell form**: `sh -c`/Git Bash/PowerShell — pipes/&&/globs work). `shell: "bash"|"powershell"`. `async: true` (background, non-blocking, no timeout enforcement), `asyncRewake: true` (stderr → Claude as system-reminder on exit 2). Stdin gets event JSON; hooks can't open `/dev/tty`.
- `http`: `url` (POST, JSON body, `Content-Type: application/json`), `headers` (env interpolation `$VAR` only if listed in `allowedEnvVars`). Non-2xx/connection failure = non-blocking; to block return 2xx + JSON decision. `allowedHttpHookUrls` setting allowlists URLs; `httpHookAllowedEnvVars` settings-level list.
- `mcp_tool`: `server` (plugin servers: `plugin:<plugin>:<server>`), `tool`, `input` (string values support `${tool_input.file_path}` substitution). Skipped at launch `SessionStart`/`Setup` (servers not up yet).
- `prompt`: `prompt` text with `$ARGUMENTS` placeholder for input JSON, optional `model`, `continueOnBlock`. Model replies `{"ok": bool, "reason": "...", "impossible": bool}` — `ok:false` blocks/ends turn per event (table in docs); `impossible:true` lets Stop events end.
- `agent`: same fields; spawns verifying subagent with tool access. Experimental; NOT supported on `PermissionRequest`.

Path placeholders in command/args/headers: `${CLAUDE_PROJECT_DIR}` (session start dir — does NOT follow worktrees; read `cwd` field instead), `${CLAUDE_PLUGIN_ROOT}`, `${CLAUDE_PLUGIN_DATA}`; also exported as env vars. Plugin `${user_config.*}` works in exec form only; shell-form alternative `$CLAUDE_PLUGIN_OPTION_<KEY>`.

## Input JSON (stdin / POST body)

Common: `session_id`, `prompt_id`, `transcript_path`, `cwd`, `scratchpad_dir`, `permission_mode` (`default|plan|acceptEdits|auto|dontAsk|bypassPermissions`; "manual" arrives as `default`), `effort.level` (`low|medium|high|xhigh|max`; also `$CLAUDE_EFFORT`), `hook_event_name`. Tool events add `tool_name`, `tool_input`, `tool_use_id`. Inside subagents: `agent_id`, `agent_type`. `SessionStart` may include `model`. Env: hook inherits parent env minus `OTEL_*`.

## Output: exit codes

- **0** = success. Stdout starting AND ending with `{`/`}` is parsed as JSON; else plain text (added as Claude-visible context only on `UserPromptSubmit`, `UserPromptExpansion`, `SessionStart`, `PostModelSwitch`; other events → debug log only). Stderr → debug log only, Claude never sees it.
- **2** = blocking error. THE ONLY code that blocks on its own — JSON can't override it. Blocking message = JSON reason or stderr. `PreToolUse` blocks the call, `UserPromptSubmit` rejects the prompt, `Stop` forces Claude to continue, `PostToolUse` shows stderr to Claude (tool already ran), etc. `PermissionRequest`, `Notification`, `SessionEnd`, `StopFailure`, `InstructionsLoaded` ignore exit 2.
- **Other** = non-blocking error: action proceeds, transcript shows `<name> hook error` + first stderr line. A missing/non-executable script lands here too — a mistyped policy hook silently does nothing. Watch for it.
- **Timeout**: hook canceled, output discarded; on `PreToolUse` a timed-out command/http/mcp_tool hook does NOT block (SDK callback hooks do block). `PreModelSwitch` timeout DOES block the switch.
- `WorktreeCreate`/`WorktreeRemove`: ANY non-zero exit fails.

## Output: JSON on stdout (exit 0)

Universal: `continue:false` (stop everything; `stopReason` message), `systemMessage` (user-visible warning), `terminalSequence` (bell/notification), `suppressOutput` (accepted, no-op). Strings capped at 10k chars each.

Top-level `decision:"block"` + `reason`: UserPromptSubmit, UserPromptExpansion, PostToolUse, PostToolUseFailure, PostToolBatch, Stop, SubagentStop, ConfigChange, PreCompact, TaskCreated.

`hookSpecificOutput` (requires `hookEventName`):
- `PreToolUse`: `permissionDecision` `allow|deny|ask|defer` + `permissionDecisionReason`; `updatedInput` rewrites tool args; `additionalContext` adds context
- `PermissionRequest`: `decision.behavior` `allow|deny`, `decision.updatedInput`, `decision.updatedPermissions` (persist allow rules)
- `PostToolUse`: `updatedToolOutput` replaces result
- `PermissionDenied`: `retry: true`
- `SessionStart`/`SubagentStart`/`PostModelSwitch`: `additionalContext` (+ SessionStart: `initialUserMessage`, `watchPaths`, `sessionTitle`, `reloadSkills`)
- `Elicitation`/`ElicitationResult`: `action` `accept|decline|cancel`, `content`
- `MessageDisplay`: `displayContent` (screen only, transcript keeps original)
- `SessionStart` can also persist env vars for the session (see docs' "Persist environment variables" / `CLAUDE_ENV_FILE`)

## Debugging hooks

- `/hooks` — read-only browser: events, matchers, source file, handler detail. Verify registration here
- `claude --debug` / `--debug='hooks'` — logs matcher eval, handler spawns, fallback dirs, mcp_tool skips
- Test script standalone: `echo '{"tool_input":{...}}' | ./hook.sh`; ensure executable + shebang
- stdout must contain ONLY the JSON — noisy shell profile output breaks parsing ("hook JSON has no effect")
- `disableAllHooks: true` (can't remove managed hooks from lower scopes; `--settings '{"disableAllHooks":true}'` overrides for a run)
- Security: hooks run with your permissions, unsandboxed; project hooks gated by workspace trust (settings-file hooks in untrusted `-p` runs DO run; subagent frontmatter hooks don't until trusted)

Per-event input schemas, matchers, and decision tables: https://code.claude.com/docs/en/hooks#hook-events
