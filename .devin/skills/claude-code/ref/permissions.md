# Claude Code permissions, modes & sandboxing

Client-enforced control over what Claude can do. Rules are enforced by Claude Code, NOT the model — CLAUDE.md instructions don't grant/revoke access.
Source: https://code.claude.com/docs/en/permissions · /permission-modes · /sandboxing · /tools-reference

## Permission modes

| Mode | Runs without asking | Use |
|---|---|---|
| `default` (UI: **Manual**) | Reads only | Review everything |
| `acceptEdits` | + file edits, `mkdir`/`touch`/`mv`/`cp` in working dirs | Iterating while reviewing |
| `plan` | Reads + classifier-approved commands; no edits until plan approved | Explore before changing |
| `auto` | Everything, classifier checks shell/network actions in background | Long tasks (default on v2.1.283+ interactive) |
| `dontAsk` | Reads + pre-approved tools; anything that'd prompt is **denied** | CI/scripts with exact allowlist |
| `bypassPermissions` | Everything | Containers/VMs only |

- Switch: `Shift+Tab` cycles modes; `--permission-mode`, `permissions.defaultMode` setting; `--dangerously-skip-permissions` = bypassPermissions; `--allow-dangerously-skip-permissions` adds it to cycle w/o starting there
- Resolution: flag > `defaultMode` > built-in default. `auto`/`bypassPermissions` in project/local settings files DON'T take effect (user/managed/`--settings` only)
- Never auto-approved in ANY mode: explicit ask rules, org-set `ask` connector tools, `AskUserQuestion` & `requiresUserInteraction` MCP tools, `rm`/`rmdir` on **critical paths**, cross-session messaging safeguards, outside-working-dir reads when `blockReadsOutsideWorkingDirectories` is on
- Deny rules apply in EVERY mode including bypassPermissions
- `bypassPermissions` skips ALL prompts incl. protected-path writes — use only inside containers/VMs, as non-root on Linux/macOS. `-p` runs under it deny the few calls that'd still prompt
- On resume: mode restored only for terminal `--continue`/`--resume` (not picker, `/resume`, or `-p`)

## Permission rules

```json
{ "permissions": { "allow": [...], "ask": [...], "deny": [...],
                   "defaultMode": "auto", "additionalDirectories": [...] } }
```

- Evaluation order: **deny → ask → allow**, first match wins. An allow can't carve an exception from a deny; an ask prompts even when an allow also matches
- Bare tool name (`"Bash"`, `"mcp__*"`) = tool removed from context entirely; scoped (`"Bash(rm *)"`) = blocks matching calls. `EndConversation` can't be removed while other tools remain
- "Yes, don't ask again" saves permanent rules to `.claude/settings.local.json` at the **repo root** (applies repo-wide, incl. worktrees/subdirs); file-edit approvals last only to session end
- `/permissions` dialog: view/manage rules live, applies next tool call same turn
- Hooks: `PreToolUse` hook decisions can't override deny/ask rules; a blocking hook (exit 2) DOES beat allow rules. For "allow everything except X": allow `"Bash"` + PreToolUse hook that denies X

### Rule syntax

`Tool` or `Tool(specifier)`:
- `Bash(npm run build)` exact · `Bash(npm run *)` prefix — `*` AFTER subcommand; trailing ` *` also matches bare command; `Bash(ls *)` ≠ `Bash(ls*)` (space required); `Bash(ls:*)` ≡ `Bash(ls *)`
- Compound commands: `&& || ; | |& &` newlines split into subcommands — rule must match EACH; deny/ask trigger if ANY subcommand matches (incl. inside `$()`, backticks, subshells, `for` bodies)
- Wrapper stripping: `timeout`, `time`, `nice`, `nohup`, `stdbuf`, `command`, `builtin`, `noglob`, bare `xargs` stripped before matching; known-safe `VAR=x` assignments stripped for allow (deny/ask match past ANY assignment). `npx`, `docker exec`, `devbox run`, `watch`, `find -exec` NOT stripped — write rules including the inner command (`Bash(devbox run npm test)`)
- `Bash` deny doesn't match path invocations (`/bin/rm`) or `sh -c 'rm'` — pair with sandbox for real enforcement
- Read-only built-ins never prompt: `ls cat echo pwd head tail grep find wc which diff stat du cd` + read-only git forms (exceptions: write-capable flags + unquoted globs, `docker -H/--context`, `file -m/-f`, UNC paths, special-var writes, unparseable/>10k-char commands). `cd X && git ...` prompts (hooks in new dir); `cd` + redirect prompts
- `Bash(param:value)` matches by input param (e.g. `run_in_background:true`) — NOT on primary fields (`command`, `file_path`, `url`)
- `Read`/`Edit` path rules = gitignore syntax. Anchors: `//path` = filesystem root, `~/` = home, `/path` = anchored at settings source dir (project settings → primary working dir; user settings → `~/.claude`), `path`/`./path` = cwd-relative. Single-segment dir: allow=`src/**` cwd-top only, deny/ask=any depth; use `**/src/**` for any-depth allow. `!` negation carves earlier rules in the SAME file only. `Read` deny also blocks Edit/Write on that path. Write rules keyed to `Edit(...)`, Glob keyed to `Read(...)` — `Write(path)`/`NotebookEdit(path)` rules are accepted but never consulted
- File rules apply to file tools + recognized Bash file commands (`cat head tail sed tee`) + redirection targets (`>`/`<`/`tee` checked against Edit rules+protected paths; `<` against Read). Do NOT cover indirect access (`grep -r`, python scripts) — use sandbox for OS-level
- `WebFetch(domain:example.com)` hostname match, `*.example.com` = subdomains only; bare `WebFetch` vs `WebFetch(domain:*)` differ: domain form also updates sandbox allowlist + covers artifact reads
- `mcp__server`, `mcp__server__tool`, `mcp__server__*`; deny/ask allow glob tool names (`mcp__*` all MCP); allow globs only after literal `mcp__<server>__` prefix. `mcp__(...)` rules in settings files are skipped — pass via `--disallowedTools`
- `Agent(Name)` deny rules disable subagents (`Agent(Explore)`)
- `Cd(pattern)` gates `/cd`; any allow rule → allowlist mode
- Symlinks: allow needs BOTH requested path and resolved target to match; deny matches EITHER. Writes where a symlinked parent resolves outside working dirs aren't auto-approved
- Answer prompts with a comment: `Tab` on Yes/No opens comment field; "No"+comment = Claude continues with your reason; bare "No" ends the turn

### Protected & critical paths

- Protected paths (writes never auto-approved; prompt/classifier/deny per mode; `permissions.allow` can't pre-approve): dirs `.git`, `.config/git`, `.vscode`, `.idea`, `.husky`, `.cargo`, `.devcontainer`, `.yarn`, `.mvn`, `.claude` (except `.claude/worktrees`); files `.gitconfig`, `.gitmodules`, shell rc files, `.envrc`, `.npmrc`/`.yarnrc`/`bunfig.toml`, `.bazelrc`, pre-commit/lefthook configs, wrapper properties, `.devcontainer.json`, `.ripgreprc`, `pyrightconfig.json`, `.mcp.json`, `.claude.json`. Session-scoped override offered in prompt
- Critical paths (`rm`/`rmdir` never auto-approved by allow rule or hook "allow" — guard against model error): `/`, top-level dirs, `~`, drive roots, cwd & parents, additional dirs & parents (glob form), `"$VAR"/*` and command-substitution targets. Applies inside nested `$(...)`, subshells, scripts too

## Working directories

File access = launch dir (primary working dir) + `additionalDirectories` setting + `--add-dir`/`/add-dir`. `/cd` moves the session (its own `Cd` rules). Added dirs grant file access only — their `.claude/` config is NOT discovered. Network/UNC paths can't be added.

## Sandboxed Bash (built-in, macOS/Linux/WSL2; not native Windows)

OS-enforced filesystem+network isolation for Bash/PowerShell/Monitor + child processes. Deps: `bubblewrap` + `socat` on Linux (Ubuntu 24.04+ needs AppArmor userns profile for bwrap); macOS uses Seatbelt; optional seccomp via `npm i -g @anthropic-ai/sandbox-runtime`.

- Enable: `/sandbox` panel (Mode/Overrides/Config/Deps tabs), or `"sandbox": {"enabled": true}`; `sandbox.failIfUnavailable` makes missing deps a hard failure
- Modes: **auto-allow** (sandboxed commands run without prompting) or regular permissions. Deny rules, critical-path `rm`, and content-scoped ask rules (`Bash(git push *)`) still apply; bare `Bash`/`Bash(*)` ask is skipped for sandboxed commands
- Defaults: write = working dir + per-user temp + additionalDirectories; new network domains prompt once (in auto mode, per-command `allowedDomains` go to the classifier)
- `sandbox.allowUnsandboxedCommands` — retry blocked commands outside sandbox (their prompts show "(unsandboxed)")
- Key keys: `sandbox.filesystem.allowRead/allowWrite/denyRead/denyWrite/disabled`, `sandbox.network.allowedDomains/deniedDomains/strictAllowlist/allowUnixSockets/allowAllUnixSockets/httpProxyPort/socksProxyPort/tlsTerminate/allowMachLookup` (macOS XPC), `sandbox.excludedCommands` (run unsandboxed), `sandbox.credentials.*` (hide/mask creds, SigV4 re-signing), `sandbox.autoAllowBashIfSandboxed`, `sandbox.bwrapPath`/`socatPath`/`ripgrep`
- WebFetch `domain:` rules feed the network allow/deny lists

## Tools (names for rules/matchers)

`Agent`, `Artifact`, `AskUserQuestion`, `Bash`, `CronCreate/Delete/List`, `Edit`, `EndConversation`, `EnterPlanMode`/`ExitPlanMode`, `EnterWorktree`/`ExitWorktree`, `Glob`, `Grep`, `ListAgents`, `ListMcpResourcesTool`, `LSP`, `Monitor`, `NotebookEdit`, `PowerShell`, `PushNotification`, `Read`, `ReadMcpResourceTool`, `RemoteTrigger`, `ReportFindings`, `ScheduleWakeup`, `SendFeedback`, `SendMessage`, `Skill`, `Task*` (task tracking), `TodoWrite`, `WebFetch`, `WebSearch`, `Write` — plus `mcp__<server>__<tool>` (plugin servers: `mcp__plugin_<plugin>_<server>__<tool>`).

Prompts in Manual mode (paths inside working dir): Bash (minus read-only set), Edit/Write/NotebookEdit, WebFetch/WebSearch, Monitor, EnterWorktree (outside `.claude/worktrees/`), ExitPlanMode, Artifact. `Glob`/`Grep` are NOT in the default Unix tool set (Claude uses Bash equivalents); `--tools` controls the set.

Full per-tool behavior notes: https://code.claude.com/docs/en/tools-reference
