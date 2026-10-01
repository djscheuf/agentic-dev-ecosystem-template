# Claude Code headless mode & Agent SDK

Running `claude` non-interactively in scripts, CI, and wrapped applications.
Source: https://code.claude.com/docs/en/headless · https://code.claude.com/docs/en/agent-sdk/overview

## Print mode basics

`claude -p "prompt"` runs once and exits. Exit 0 on success, non-zero on failure; invalid flags → stderr, runtime failures → result field on stdout. Stdin is piped context (10MB cap — larger inputs: write to a file and reference the path).

```bash
claude -p "Find and fix the bug in auth.py" --allowedTools "Read,Edit,Bash"
cat build.log | claude -p "explain the root cause" > out.txt
session_id=$(claude -p "Start a review" --output-format json | jq -r '.session_id')
claude -p "Continue" --resume "$session_id"   # works from any directory
claude -p "follow up" --continue              # -p continue DOES include -p/SDK sessions
```

Incompatible: `--bg` (rejected), `--cloud <task>` (rejected; `--cloud <session-id> -p` queues a message instead).

## Output formats (`--output-format`, `-p` only)

- `text` — plain response
- `json` — single JSON object: `result` text, `session_id`, `total_cost_usd` + per-model breakdown (client-side estimates), usage; pair with `--json-schema '<schema>'` for validated `structured_output` field (`format` keyword accepted as annotation only)
- `stream-json` — NDJSON events: `system/init` first (model, tools, `mcp_servers[]`+`status`, `mcp_server_errors[]`, `plugins[]`, `plugin_errors[]`, `capabilities[]`), then message events, final `result` line. Always add `--verbose`; `--include-partial-messages` for token deltas (`stream_event` / `text_delta`); slow consumers get up to 30s drain time
- Stream extras: `--forward-subagent-text` (or `CLAUDE_CODE_FORWARD_SUBAGENT_TEXT`) emits subagent text/thinking as messages with `parent_tool_use_id`; `--include-hook-events` adds `hook_started/progress/response`; `--replay-user-messages` echoes stdin; `--prompt-suggestions` emits predicted next prompts; `system/api_retry` events report retry attempts; `permission_denied` messages list denials
- `--input-format stream-json` — multi-turn conversations by writing message JSON to stdin (queued messages at `--max-turns` boundary start a new turn)

## Bare mode — recommended for scripts

`--bare` skips auto-discovery of hooks, skills, commands, subagents, plugins, MCP servers, auto memory, CLAUDE.md → faster, reproducible across machines. Sets `CLAUDE_CODE_SIMPLE`. Anthropic auth requires `ANTHROPIC_API_KEY` or `apiKeyHelper` in `--settings` (no OAuth/keychain read). Tools: Bash + file read/edit. Still loads: `--add-dir`'s `.claude/skills/` (not commands/agents), and anything passed via `--settings`, `--mcp-config`, `--agents`, `--plugin-dir`, system-prompt flags. Slated to become the `-p` default.

Contrast `--safe-mode` (customizations off but auth/model/permissions normal — for troubleshooting) and `--restricted` (eval harness: no command tools, file tools confined to working dirs, only managed+`--settings` config).

⚠️ Without `--bare`, `-p` still runs project settings hooks and `.mcp.json` servers — NO trust dialog or approval prompt is shown. Use `--bare` or `--strict-mcp-config`/`--setting-sources` on untrusted trees.

## Permissions in scripts

- `-p` defaults to Manual permission mode — always set one explicitly
- `--allowedTools "Bash(git diff *)..."` — permission-rule syntax, trailing ` *` = prefix match (space matters)
- `--permission-mode dontAsk` — deny anything that'd prompt (CI allowlist pattern: `dontAsk --allowedTools "Bash(npm test)" "Read"`)
- `--permission-mode auto` — classifier reviews shell/network actions
- `--dangerously-skip-permissions` — containers/VMs only
- `--permission-prompts none` — don't wait on a prompt host (SDK `canUseTool` or `--permission-prompt-tool`); denies unresolved prompts, removes `AskUserQuestion`, cancels unanswered MCP elicitations. v2.1.259+
- `--permission-prompt-tool <mcp_tool>` — an MCP tool decides prompts
- `--max-turns`, `--max-budget-usd` (subagent spend counts), `--no-session-persistence`

## Process/session lifecycle for wrappers

- SIGTERM → exit 143, turn left unfinished, only `SessionEnd` hooks run; use SIGINT/SDK `interrupt()` to end the turn cleanly. `CLAUDE_CODE_RESUME_INTERRUPTED_TURN=1` makes resume retry the cut-off call
- Background Bash tasks killed ~5s after final result; background subagents/workflows hold the process until done (idle cap `CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS`, 10min default, `0`=forever)
- Deleted cwd mid-run: session continues, shell commands fail until dir returns
- `-p` sessions are excluded from interactive `--continue` and the picker but resumable by `--resume <id>`; transcripts still in `~/.claude/projects/`
- `--session-id <uuid>` fixes the ID; `--fork-session` new ID on resume
- System prompt flags: `--system-prompt[-file]` (replace), `--append-system-prompt[-file]` (extend), `__SYSTEM_PROMPT_DYNAMIC_BOUNDARY__` line splits static/dynamic parts for cache reuse, `--exclude-dynamic-system-prompt-sections` for multi-user scripts, `--system-prompt-snapshot off` to rebuild each request
- In `-p`, slash commands in the prompt expand (`/my-skill`); terminal-only commands unavailable; `/model`, `/effort`, `/config key=value`, `/output-style` work with args
- `--init`, `--maintenance`, `--init-only` run Setup/SessionStart hooks for CI preparation
- Long-lived auth for CI: `claude setup-token` → `CLAUDE_CODE_OAUTH_TOKEN` (subscription) or `ANTHROPIC_API_KEY`/`apiKeyHelper`

## Agent SDK

Same agent loop/tools/hooks/sessions as the CLI, as a library: Python (`claude-agent-sdk`) and TypeScript (`@anthropic-ai/claude-agent-sdk`). Use it when you need in-process control: `canUseTool` approval callbacks, streaming message objects, structured outputs via Zod/Pydantic, in-process MCP tool servers, session continue/resume/fork, custom system prompts. For other languages, drive `claude -p --output-format stream-json` as a subprocess — that's what the SDK does under the hood.

Alternatives: Client SDK (raw API, you write the loop), Managed Agents (Anthropic-hosted harness). Licensing note: third-party products can't offer claude.ai login/rate limits — use API key auth.

Docs: https://code.claude.com/docs/en/agent-sdk/quickstart · /typescript · /python · /hooks · /permissions · /sessions · /structured-outputs · /mcp · /subagents · /streaming-vs-single-mode
