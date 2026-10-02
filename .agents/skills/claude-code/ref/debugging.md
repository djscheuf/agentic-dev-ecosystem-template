# Debugging Claude Code

Diagnosing configuration, hooks, MCP, performance, and runtime errors.
Source: https://code.claude.com/docs/en/debug-your-config · /troubleshooting · /errors · /troubleshoot-install

## First-line inspection commands

Run inside a session (or `claude doctor` / `claude --debug` from the shell):

| Command | Shows |
|---|---|
| `/context` | Everything in the context window: system prompt, tools, MCP tools, subagents (with source), memory files, skills, messages — confirm your file loaded *at all* |
| `/status` | Active settings sources, whether managed settings are in effect |
| `/doctor` | Checkup: install health, invalid settings files, unused extensions, duplicate subagent names, bloated checked-in CLAUDE.md; proposes fixes |
| `/memory` `/skills` `/hooks` `/mcp` `/permissions` | What's actually loaded per feature |
| `/debug [issue]` | Debug logging for the session + Claude self-diagnosis |
| `/doctor` (shell: `claude doctor`) | Read-only diagnostics without starting a session |
| `claude --debug`, `--debug=mcp` | Full debug log to `~/.claude/debug/<session-id>.txt` — hook evaluations, matcher checks, exit codes, MCP stderr |
| `/heapdump` | Writes `<session-id>.heapsnapshot` + `-diagnostics.json` to `~/Desktop` (home on Linux). ⚠️ heapsnapshot contains conversation + credentials — share only the `-diagnostics.json` |

`--debug` ignores `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC`. Ctrl+O in-session toggles verbose (tool expansion) — see cli-usage.md.

## The core isolation test

```bash
claude --safe-mode                       # all customizations off; auth/permissions normal
cd /tmp && CLAUDE_CONFIG_DIR=/tmp/claude-clean claude   # nothing loads: no settings, hooks, MCP, plugins, memory
```

- Still broken in safe mode → binary/install/provider issue (`claude doctor`, `troubleshoot-install`)
- Fixed in safe mode, broken in clean-config → managed/policy layer
- Fixed in clean config → bisect your `~/.claude` and project `.claude` files back in one at a time

## Common failure patterns

**Settings not applying** → precedence override (local > project > user; env vars/flags on top; managed beats all). `/status` shows which sources are active. Settings edits hot-reload into a running session (brief file-stability delay) — `/hooks` may need a re-open to refresh.

**Hooks not firing** — see hooks.md debugging section. Key traps:
- `matcher` is a single string: `"Edit|Write"` or `"Edit,Write"` (`,` only works v2.1.191+); a `matcher` *array* is a schema error that rejects the whole settings file (managed settings: drops the `hooks` key). `claude doctor` reports it
- Misspelled tool name = matcher silently matches nothing
- Hooks live under `"hooks"` in settings.json, not a standalone file
- Debug: `claude --debug` logs each event, matchers checked, hook exit code/output. `--debug-hooks-json` on stderr

**MCP servers** — `/mcp` shows status: project `.mcp.json` servers need one-time approval (dismissed prompt = disabled until approved via `/mcp`); `Failed` often = relative path in `command`/`args` resolving against launch dir, not `.mcp.json` location; `Connected, 0 tools` → Reconnect, then `claude --debug=mcp` for the server's stderr. `-p` mode: check `mcp_server_errors` in `system/init` (skipped entries exit cleanly — CI-gate on it).

**Skill/subagent not appearing** — check `/skills`, `/context`; frontmatter must start on line 1 with valid YAML (unparseable = silently fieldless, `claude plugin validate` catches it in agents). 15k-token aggregate subagent description cap → startup warning.

## Runtime error map (see /errors for the full index)

- `API Error: 5xx` / `Repeated 529 Overloaded` / `<model> high load` — server-side; Claude retries w/ backoff (`system/api_retry` events in stream-json); switch model with `/model` or wait
- `Request timed out` / `No response from API` / mid-response stall messages — retry; persistent → check network/proxy/`API_TIMEOUT_MS`
- `Agent terminated early due to an API error` — retry limit hit
- `Auto mode` classifier errors (`...cannot determine the safety...`, `no safety verdict` ×10 → auto mode disabled) — rerun or switch permission mode
- `You've hit your session/weekly/Opus/Sonnet limit`, `Request rejected (429)`, `Credit balance too low`, spend-limit messages — wait for reset, `/upgrade`, or adjust limits
- Auth: `Not logged in` → `/login`; `Invalid API key`; `Your apiKeyHelper script is failing` (check the script + `apiKeyHelperTtlMs`); `Invalid ANTHROPIC_CUSTOM_HEADERS`; `OAuth token revoked/expired` → `/login`; `organization disabled API key/subscription` → policy
- `There's an issue with the selected model` / `model not found` → `/model` pick another
- `Your disk quota is full` / `ENOSPC` / `Command output was lost` — free disk space (transcripts, `/tmp`, caches)
- `Claude Code process exited with code N` (VS Code/SDK wrapper) — wrapper-side crash; get the real error by running `claude` directly or reading the debug log
- `command not found`, `EACCES`, TLS errors, OAuth login loops → `troubleshoot-install` page

## Performance & stability

- High CPU/RAM: `/compact` often; restart between tasks; `.gitignore` huge dirs; `--safe-mode` to bisect plugins/MCP. Heap >2.5GB → critical warning → restart + `claude --continue`; still high → `/heapdump`
- `Autocompact is thrashing...` → compaction refilled immediately: read oversized files in chunks, `/compact keep only the plan and the diff`, offload to a subagent, or `/clear`
- Hangs → Ctrl+C; else restart and `claude --resume` (conversation survives)
- Garbled glyphs in integrated terminals → `/terminal-setup` (disables GPU acceleration)
- `claude -p` exits silently / empty output → check exit code, stderr for flag errors, `result` field for runtime failures (see headless-and-sdk.md)

## Reporting bugs

`claude issue` (or `/issue`) files a GitHub issue with diagnostics; redact sensitive paths. `/bug` describes without filing. Bugs/features: https://github.com/anthropics/claude-code/issues — attach `-diagnostics.json` only, never `.heapsnapshot`.
