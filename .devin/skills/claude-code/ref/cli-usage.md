# Claude Code CLI usage

Commands, flags, interactive commands, and session management for the `claude` CLI.
Source: https://code.claude.com/docs/en/cli-reference · https://code.claude.com/docs/en/commands · https://code.claude.com/docs/en/sessions · https://code.claude.com/docs/en/interactive-mode

## Entry points

| Command | Effect |
|---|---|
| `claude` | Interactive session in cwd |
| `claude "query"` | Interactive session with initial prompt |
| `claude -p "query"` | Print mode: run once, output, exit (scripting) |
| `cat f \| claude -p "q"` | Pipe stdin into a print-mode query |
| `claude -c` / `--continue` | Resume most recent conversation in cwd (skips `-p`/SDK sessions) |
| `claude -r <id\|name>` / `--resume` | Resume by session ID/name, or opens picker with no arg |
| `claude --from-pr <n>` | Picker filtered to sessions linked to a PR |
| `/resume` | Switch conversation inside a running session |

Other subcommands: `claude update`, `claude install [ver|stable|latest]`, `claude auth login|logout|status` (`status` → JSON, exit 0 if logged in), `claude doctor` (read-only diagnostics without a session), `claude mcp` (+ `login`/`logout`), `claude plugin`, `claude agents` (agent view; `--json` for scripting), `claude attach|logs|stop|rm|respawn <id>` (background sessions), `claude daemon status|stop`, `claude setup-token` (long-lived OAuth token for CI), `claude project purge [path]` (`--dry-run` first), `claude remote-control`, `claude ultrareview`.

## Key flags

`claude --help` is NOT exhaustive — absence from help ≠ unavailable.

**Mode/behavior**
- `--print`, `-p` — non-interactive; required for scripting
- `--output-format text|json|stream-json` — print-mode output
- `--input-format text|stream-json` — print-mode input (stream-json = multi-turn via stdin)
- `--verbose` — required to see stream-json internals
- `--permission-mode default|acceptEdits|plan|auto|dontAsk|bypassPermissions` (`manual` = alias for default)
- `--dangerously-skip-permissions` — = `--permission-mode bypassPermissions`
- `--allow-dangerously-skip-permissions` — adds bypassPermissions to Shift+Tab cycle without starting in it
- `--tools "Bash,Edit,Read"` / `""` / `"default"` — restrict built-in tool set (doesn't affect MCP tools)
- `--allowedTools` / `--disallowedTools` — permission allow/deny rules, e.g. `"Bash(git log *)"`; bare name removes tool entirely; `"mcp__*"` denies all MCP tools
- `--restricted` — eval-harness mode: no command tools, only managed+`--settings` config, file tools confined to working dirs
- `--bare` — minimal mode: skips hooks, skills, CLAUDE.md, MCP, plugins, memory (fast scripted startup; sets `CLAUDE_CODE_SIMPLE`)
- `--safe-mode` — all customizations off for troubleshooting, but auth/model/permissions still work (sets `CLAUDE_CODE_SAFE_MODE`)
- `--bg` / `--background` — start as background agent, return immediately; can't combine with `-p`
- `--worktree, -w [name\|#PR]` — run in isolated git worktree at `<repo>/.claude/worktrees/<name>`; `--tmux` for tmux session
- `--add-dir <paths>` — grant file access to extra dirs (does NOT load their `.claude/` config)

**Config injection (answers "can config be passed via CLI?" — yes)**
- `--settings <file-or-inline-JSON>` — overrides settings.json keys for this session (file ≤ 2 MiB)
- `--setting-sources user,project,local` — which settings files to load
- `--mcp-config <files-or-JSON>` — load MCP servers ad hoc; `--strict-mcp-config` = use ONLY these
- `--plugin-dir` / `--plugin-url` — session-only plugin loading
- `--agents '<json>'` — define subagents inline (`-p` accepts a JSON file path)
- `--agent <name>` — run session as a subagent
- `--model <alias|id>` (`sonnet`, `opus`, `haiku`, `fable`, full ID) — overrides `model` setting & `ANTHROPIC_MODEL`
- `--effort low|medium|high|xhigh|max|ultracode`, `--fallback-model a,b`, `--autocompact auto|<tokens>` (e.g. `500k`)
- `--system-prompt` / `--system-prompt-file` — replace system prompt; `--append-system-prompt` / `--append-system-prompt-file` — extend it (replace vs append are mutually exclusive per pair, appends combinable). `--system-prompt-snapshot off` rebuilds prompt each request
- `--append-subagent-system-prompt[-file]` — extra prompt text for all subagents (`-p` only)
- `--name, -n <name>` — session display name (resumable via `-r <name>`)
- `--session-id <uuid>`, `--fork-session` (new ID on resume), `--no-session-persistence` (`-p` only)

**Print-mode / SDK controls**
- `--max-turns <n>`, `--max-budget-usd <n>` — hard limits; subagent spend counts toward budget
- `--json-schema <schema>` — validated structured JSON output at end
- `--include-partial-messages`, `--include-hook-events`, `--forward-subagent-text`, `--replay-user-messages`, `--prompt-suggestions` — stream-json extras
- `--permission-prompt-tool <mcp-tool>` — MCP tool answers permission prompts; `--permission-prompts none` — deny all prompts (unattended)
- `--init` / `--maintenance` — run Setup hooks with matcher (`-p` only); `--init-only` — run Setup+SessionStart hooks then exit
- `--exclude-dynamic-system-prompt-sections` — better prompt-cache reuse across users (`-p` scripts)
- `--debug[='cat1,cat2']`, `--debug-file <path>` — debug logging
- `--chrome` / `--no-chrome`, `--ide`, `--channels`, `--cloud`, `--teleport`, `--remote-control/--rc`, `--environment <ccpool_...>`, `--teammate-mode`, `--advisor <model>`, `--ax-screen-reader`

## In-session slash commands (most-used)

Type `/` for the menu; commands only recognized at message start; queue mid-turn.
- Setup: `/init` (generate CLAUDE.md), `/memory`, `/mcp`, `/permissions`, `/config`, `/add-dir <path>`
- Model/context: `/model`, `/effort`, `/context` (what's filling the window), `/compact`, `/autocompact`, `/clear`
- Work: `/plan`, `/tasks` (bg shells+subagents), `/background` (`/bg`), `/batch`, `/diff`, `/rewind` (checkpoint rollback)
- Review: `/code-review [--fix|high <pr>|ultra]`, `/security-review`
- Sessions: `/resume`, `/branch`, `/fork`, `/rename`, `/cd`, `/export`
- Help/debug: `/doctor`, `/debug`, `/hooks`, `/status`, `/usage`, `/cost`, `/feedback`, `/btw` (side question, no history)

## Keyboard shortcuts (essentials)

- `Esc` interrupt turn; `Esc Esc` rewind menu (empty input) or clear draft (with text)
- `Ctrl+C` interrupt → clear input → exit; `Ctrl+D` exit (2 presses); `Ctrl+Z` suspend
- `Shift+Tab` cycle permission modes (default→acceptEdits→plan→bypassPermissions→auto)
- `Alt+P` model switch · `Alt+T` extended thinking · `Alt+O` fast mode · `Ctrl+O` transcript viewer
- `Ctrl+B` background task · `Ctrl+G`/`Ctrl+X Ctrl+E` edit prompt in $EDITOR · `Ctrl+S` stash prompt · `Ctrl+R` history search
- `!` prefix = shell mode (run bash directly); `@` file path autocomplete; `#` prefix = append to memory
- macOS: Alt/Option shortcuts need "Option as Meta" in terminal settings

## Sessions: what restores on resume

Restored: full conversation+tool calls, model, agent, permission mode (terminal resumes only — picker/`/resume`/`-p` don't restore it), active goal, unexpired scheduled tasks.

NOT restored: `--mcp-config`, `--settings`, `--plugin-dir`, `--fallback-model`, `--add-dir` dirs — **re-pass these flags when resuming**. Files-based settings (settings.json etc.) reload automatically. `-p`/SDK sessions are hidden from picker and `--continue`, but resumable by explicit ID; `claude -p --continue` does include them.

Transcripts: `~/.claude/projects/<slug>/<session-id>.jsonl`.
