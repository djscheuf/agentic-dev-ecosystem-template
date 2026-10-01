# Extending Claude Code

Skills, subagents, MCP servers, plugins — what to use when, and how to write them.
Source: https://code.claude.com/docs/en/features-overview · /skills · /sub-agents · /mcp · /plugins/overview

## Pick the right mechanism

- **CLAUDE.md** — always-on project conventions/facts; loads every session (<200 lines)
- **Skill** — reusable instructions/workflows loaded on demand (`/name` or auto by description); body costs no context until used
- **Subagent** — isolated worker, own context window, returns summary; use when a task would flood your context
- **Hook** — deterministic automation on lifecycle events (see hooks.md)
- **MCP** — external tools/data (databases, trackers, Slack, browsers)
- **Output style** — session-wide persona/format (`outputStyle`, `~/.claude/output-styles/`)
- **Plugin** — packages skills+hooks+agents+MCP into an installable, shareable unit (`/plugin`, marketplaces, `/my-plugin:name` namespacing)

Rule of thumb: repeated mistake → CLAUDE.md; procedure you keep pasting → skill; reads many files but you only need the answer → subagent; must run every time → hook; external system → MCP; reuse across repos/team → plugin.

## Skills

Locations: `~/.claude/skills/<name>/SKILL.md` (personal), `.claude/skills/<name>/SKILL.md` (project), plugin `skills/`, `.claude/commands/<name>.md` (legacy single-file form — same mechanism). Invoke: `/name [args]` or Claude auto-loads by `description` match. `/skill-a /skill-b <text>` chains up to 6.

Frontmatter (`---` must be first line; unparseable YAML = no fields, no error):
| Field | Effect |
|---|---|
| `name` | Command name (default: dir name) |
| `description` | When to use — drives auto-invocation; desc+when_to_use truncated at 1,536 chars in listing |
| `argument-hint` | Autocomplete hint, e.g. `[issue-number]` |
| `arguments` | Named arg list → `$name` placeholders; positional `$1`/`$ARGUMENTS` also available |
| `disable-model-invocation` | `true` = only humans can `/invoke` (hidden from Claude) |
| `user-invocable` | `false` = only Claude invokes (hidden from `/` menu) |
| `allowed-tools` | Tools pre-approved during the skill's turn (clears next message) |
| `disallowed-tools` | Removes tools while skill is active |
| `model` | Model for this skill's turn (or `inherit`) |
| `context` | `fork` = run in isolated subagent |
| `agent` | Which subagent type when `context: fork` |
| `background` | `false` = forked skill blocks turn (default: runs in background) |
| `hooks` | Hooks registered for rest of session (see hooks.md; `once:true` supported) |
| `shell` | `bash`/`powershell` for injected commands |
| `metadata`, `license`, `compatibility` | Spec fields; Claude Code accepts, doesn't act |

Content features: `!`cmd`` dynamic injection (runs command, inlines output before Claude sees the skill), `${CLAUDE_SKILL_DIR}` / `${CLAUDE_PLUGIN_ROOT}` / `${CLAUDE_PLUGIN_DATA}` / `${CLAUDE_PROJECT_DIR}` substitution (also inside `allowed-tools` Bash rules — lets bundled scripts run prompt-free), supporting files bundled in the skill dir. Inject failures: `shell: bash` fails outright without bash (Windows w/o Git Bash); command failures surface as errors Claude sees.

`skillOverrides` setting (or `/skills` menu, Space to cycle) hides/disables skills w/o editing files. `disableBundledSkills` turns off built-ins (`/doctor`, `/code-review`, `/debug`, `/loop`, `/claude-api`, etc.). `disableSkillShellExecution` blocks `!` injections everywhere. Synced claude.ai skills: `syncClaudeAiSkills`.

## Subagents

Files: `.claude/agents/*.md` or `~/.claude/agents/*.md` (recursive scan; identity = `name` field). `--agents '<json>'` defines them ad hoc; `claude plugin validate <dir>` checks frontmatter parse errors.

Frontmatter (camelCase; unknown fields silently ignored; `name`+`description` required, `:` forbidden in names):
- `tools` (allowlist) / `disallowedTools` (denylist; applied first) — comma string or YAML list; `mcp__server`/`mcp__server__*` patterns OK; `mcp__*` = all MCP
- `model` — `sonnet|opus|haiku|fable|inherit|full-id` (order: invocation param > frontmatter > `CLAUDE_CODE_SUBAGENT_MODEL` > main model)
- `permissionMode` — `default|acceptEdits|auto|dontAsk|bypassPermissions|plan` (plugin agents: ignored)
- `maxTurns` (partial output on cap; resumable), `effort`, `skills` (preload skill content), `mcpServers` (scoped MCP), `hooks` (scoped lifecycle hooks), `memory` (`user|project|local` persistent agent memory), `background: true`, `omitClaudeMd: true` (skip CLAUDE.md loading), `isolation: worktree` (temp git worktree), `color`, `initialPrompt` (first-turn prompt when run via `--agent`), `experimental.cacheTtl`

Tool pool: subagents never get `AskUserQuestion`, `EndConversation`, `EnterPlanMode`, `ScheduleWakeup`, `WaitForMcpServers`, `Workflow`, `Agent` at depth limit, `ExitPlanMode` (unless `permissionMode: plan`). Background subagents (the default) keep a reduced built-in set: Read, Grep, Glob, LSP, Bash, PowerShell, Edit, Write, NotebookEdit, WebFetch, WebSearch, TodoWrite, Skill, ToolSearch, EnterWorktree, ExitWorktree, Monitor, TaskStop, SendMessage, Artifact + all MCP tools. Forks get the parent's exact pool.

Built-ins: `Explore` (read-only search, inherits model capped at Opus; override w/ own `Explore` + `model: haiku`), `Plan` (read-only plan-mode research), `general-purpose` (full tools), `claude` (catch-all), `statusline-setup`, `claude-code-guide`. Restrict: `Agent(Name)` deny rules, `CLAUDE_CODE_DISABLE_EXPLORE_PLAN_AGENTS=1`, `CLAUDE_AGENT_SDK_DISABLE_BUILTIN_AGENTS=1`. Descriptions >15k tokens total → startup warning; keep descriptions short, detail in the body (system prompt).

Run as main agent: `claude --agent <name>` or `agent` setting — replaces default system prompt, keeps tool restrictions; `initialPrompt` auto-submits. Delegation: Claude routes by `description`; explicit invocation "use the X subagent" also works. Hooks: `SubagentStart`/`SubagentStop` matchers = agent name (`^plugin:name$` anchor for plugin agents). Frontmatter hooks need workspace trust for project-level agents. Resume: `SendMessage` to agent ID/name.

## MCP servers

Transports:
- **HTTP** (recommended): `claude mcp add --transport http <name> <url> [--header "K: V"]`; JSON `"type": "http"` (alias `streamable-http`). Entry with `url` but no `type` = read as stdio → skipped w/ error
- **SSE** (deprecated): `--transport sse`; `--transport http` auto-falls-back to SSE on v2.1.265+
- **stdio** (local process): `claude mcp add --env K=V --transport stdio <name> -- <cmd> [args]` — `--` separates Claude's flags from server args; gets `CLAUDE_PROJECT_DIR` env
- **WebSocket**: `type: "ws"` in JSON/`add-json` only; header-auth only, no OAuth, doesn't appear in `claude mcp list`
- `type: "sdk"` — only SDK host apps can register; skipped from config files

Scopes (highest precedence first): `local` (default; `~/.claude.json` per-project — NOTE: not `.claude/settings.local.json`) > `project` (`.mcp.json` at root, committed; interactive sessions prompt for approval, `-p`/SDK/cloud auto-approve) > `user` (`~/.claude.json`, all projects) > plugin-provided > claude.ai connectors; `managedMcpServers` outranks all. Duplicate names: whole entry from highest scope wins (no merge).

`.mcp.json` env expansion `${VAR}` / `${VAR:-default}` works in `command`, `args`, `env`, `url`, `headers` — keeps secrets out of VCS.

Approval/trust: `.mcp.json` approvals only count after workspace trust (`claude` + accept dialog); `enableAllProjectMcpServers`/`enabledMcpjsonServers` in committed settings are ignored untrusted. `disabledMcpjsonServers` blocks in every mode; `--strict-mcp-config` uses only `--mcp-config` servers; `claude mcp reset-project-choices` resets approvals. Per-project enable/disable lists live in `~/.claude.json` (`enabledMcpServers`/`disabledMcpServers`, toggled via `/mcp`).

Commands: `claude mcp list` (health: ✔ Connected / ! Needs auth / ✘ Failed + issue detail), `claude mcp get <name>`, `add`, `add-json`, `remove`, `login <name>` (OAuth; `--no-browser` for SSH), `logout`. `/mcp` in-session panel. `--mcp-config` + `-p` waits for pending servers up to `MCP_TIMEOUT` (30s default); `--permission-prompt-tool` similarly waits.

Tools appear as `mcp__<server>__<tool>` (plugin servers: `mcp__plugin_<plugin>_<server>__<tool>`). Permission rules, `allowedMcpServers`/`deniedMcpServers` settings, org `ask` flags apply normally. `requiresUserInteraction`-marked tools can't be auto-approved. Tool output caps: warn 10k tokens, hard cap `MAX_MCP_OUTPUT_TOKENS` (25k default). Timeouts: `MCP_TIMEOUT` (startup), `MCP_TOOL_TIMEOUT` (per-call, ~28h default; per-server `"timeout"` ms field overrides; progress doesn't extend), idle abort `CLAUDE_CODE_MCP_TOOL_IDLE_TIMEOUT` (5min remote/30min stdio default). Tool search is on by default — deferred schemas; `ENABLE_TOOL_SEARCH`.

Common gotchas: hidden whitespace in config values (warned, not trimmed), same name in multiple scopes, reserved names (`workspace`, `claude-in-chrome`, `computer-use`, `Claude Preview`, `Claude Browser`), missing `${VAR}` (warned, loads unexpanded).

## Plugins (pointer)

Bundle of skills/hooks/agents/MCP/output-styles installed from marketplaces: `claude plugin install <name>@<marketplace>`, `/plugin` UI, `--plugin-dir`/`--plugin-url` for one session, `enabledPlugins` setting. Components live under `<plugin>/` dirs mirroring `.claude/`; skills namespaced `/plugin:name`; plugin agents can't use `hooks`/`mcpServers`/`permissionMode`/`initialPrompt` frontmatter. Details: https://code.claude.com/docs/en/plugins/overview
