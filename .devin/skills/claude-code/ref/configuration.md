# Claude Code configuration

Settings files, precedence, `.claude` layout, memory files, env vars, model config.
Source: https://code.claude.com/docs/en/settings · /settings-reference · /claude-directory · /memory · /env-vars · /model-config

## Settings precedence (highest wins)

1. **Managed settings** — `managed-settings.json`, MDM, or claude.ai console (org-deployed; per-OS paths differ)
2. **Command line** — `claude --settings <file-or-inline-JSON>` (session-only)
3. **Project local** — `.claude/settings.local.json` (gitignored, personal)
4. **Shared project** — `.claude/settings.json` (commit this)
5. **User** — `~/.claude/settings.json` (all your projects)

Arrays (e.g. `permissions.allow`) **merge** across scopes; scalars use the most specific value.
`--setting-sources user,project,local` limits which files load. `claude auth status` prints the active `configDirectory` (`CLAUDE_CONFIG_DIR` overrides `~/.claude`).

## `.claude/` directory layout

Project `<repo>/.claude/` (mostly committed):
- `settings.json`, `settings.local.json` (gitignored)
- `rules/*.md` — topic instructions; `paths:` YAML frontmatter scopes a rule to file globs (e.g. `src/**/*.{ts,tsx}`); no `paths` = always loaded; supports symlinks
- `skills/<name>/SKILL.md` + supporting files
- `commands/<name>.md` — single-file `/name` commands (same mechanism as skills; prefer skills for new work)
- `agents/<name>.md` — subagent definitions
- `output-styles/`, `workflows/`, `agent-memory/<agent>/MEMORY.md`

Project root (NOT inside `.claude/`): `CLAUDE.md` (or `.claude/CLAUDE.md`), `CLAUDE.local.md` (gitignore it), `.mcp.json` (shared MCP servers; use `"${VAR}"` refs for secrets), `.worktreeinclude` (gitignore-syntax list of files to copy into new worktrees).

User `~/.claude/`: `settings.json`, `CLAUDE.md`, `keybindings.json`, `themes/`, `rules/`, `skills/`, `commands/`, `agents/`, `output-styles/`, `workflows/`, `projects/<slug>/<session>.jsonl` (transcripts), `projects/<slug>/memory/MEMORY.md` (auto memory). `~/.claude.json` = app state + user-scoped MCP servers.

Cleanup: `claude project purge [path] --dry-run` deletes local state for a project. `cleanupPeriodDays` controls transcript retention.

## CLAUDE.md / AGENTS.md memory files

Load order (broadest→specific): managed policy (`/etc/claude-code/CLAUDE.md` on Linux, `/Library/Application Support/ClaudeCode/` macOS) → `~/.claude/CLAUDE.md` → `./CLAUDE.md` or `./.claude/CLAUDE.md` (+ ancestors) → `./CLAUDE.local.md`. Subdirectory CLAUDE.md files load on demand when Claude reads files there.

- Target <200 lines; concrete verifiable instructions ("Run `npm test` before committing", not "test changes")
- `@path/to/file` imports other files (relative to the importing file; recursion ≤4 hops; escape spaces with `\`); imported content loads at launch too — doesn't save context
- `AGENTS.md` is read only when no CLAUDE.md/CLAUDE.local.md exists (default `claude-md-or-agents-md`); change via `/config` → Project instructions or `pluginConfigs."agents-md@builtin".options.instructionFiles` = `claude-md-and-agents-md|claude-md|managed-only`
- `claudeMdExcludes: ["**/path/CLAUDE.md"]` skips specific memory files (glob on absolute paths)
- Managed `claudeMd` key injects org instructions from managed settings
- `/init` generates a starter CLAUDE.md; `/memory` edits it; `/doctor prompt-audit` checks instruction files for conflicts
- CLAUDE.md is *guidance*, not enforcement — use `permissions.deny` / hooks for hard rules

**Auto memory**: Claude writes its own learnings to `~/.claude/projects/<slug>/memory/MEMORY.md` (+ topic files when long). First 200 lines/25KB load each session. Toggle: `autoMemoryEnabled`, relocate: `autoMemoryDirectory`.

## Environment variables

Set in shell before `claude`, or persist via `"env": {"VAR": "val"}` in any settings.json (settings-file `env` overrides the shell value; empty string = unset for provider selection). Boolean vars: `1`/`true` on, `0`/`false` off — but `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC`, `DISABLE_TELEMETRY`, `DISABLE_ERROR_REPORTING`, `IS_DEMO` etc. treat ANY non-empty value (incl. `0`) as on.

Key variables:
- `ANTHROPIC_API_KEY` — API key auth; overrides subscription (interactive: prompts once; `-p`: always used)
- `ANTHROPIC_AUTH_TOKEN` — custom `Authorization: Bearer` header
- `ANTHROPIC_BASE_URL` — route through proxy/gateway (disables Remote Control + MCP tool search unless host is api.anthropic.com)
- `ANTHROPIC_MODEL`, `ANTHROPIC_DEFAULT_{OPUS,SONNET,HAIKU,FABLE}_MODEL`, `ANTHROPIC_SMALL_FAST_MODEL`, `ANTHROPIC_DEFAULT_MODEL` — model selection/overrides (flag `--model` and `/model` beat `ANTHROPIC_MODEL`)
- `CLAUDE_CODE_EFFORT_LEVEL` — overrides `--effort` and `/effort` (note reversed precedence vs model)
- `CLAUDE_CONFIG_DIR` — move `~/.claude` elsewhere
- `CLAUDE_CODE_SIMPLE` (= `--bare`), `CLAUDE_CODE_SAFE_MODE` (= `--safe-mode`)
- `CLAUDE_CODE_USE_BEDROCK` / `_VERTEX` / `_FOUNDRY` / `_MANTLE` / `_USE_ANTHROPIC_AWS` — provider selection
- `API_TIMEOUT_MS`, `BASH_DEFAULT_TIMEOUT_MS`, `BASH_MAX_TIMEOUT_MS`, `BASH_MAX_OUTPUT_LENGTH`, `MCP_TIMEOUT`, `MCP_TOOL_TIMEOUT`, `MAX_THINKING_TOKENS`, `CLAUDE_CODE_MAX_OUTPUT_TOKENS`, `CLAUDE_CODE_MAX_TURNS`
- `HTTP_PROXY`, `HTTPS_PROXY`, `NO_PROXY`; `CLAUDE_CODE_CLIENT_CERT`/`CLIENT_KEY` (mTLS), `CLAUDE_CODE_CERT_STORE`
- `DISABLE_AUTOUPDATER`, `DISABLE_AUTOUPDATES`, `DISABLE_PROMPT_CACHING`, `DISABLE_TELEMETRY`, `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC` (kill all non-essential network calls)
- `CLAUDE_CODE_OAUTH_TOKEN` — from `claude setup-token`, for CI
- `CLAUDE_CODE_SKIP_PROMPT_HISTORY` — don't save `-p` sessions; `CLAUDE_CODE_FORWARD_SUBAGENT_TEXT`; `CLAUDE_CODE_DEBUG_LOGS_DIR`, `CLAUDE_CODE_DEBUG_LOG_LEVEL`
- `CLAUDE_CODE_GIT_BASH_PATH` (Windows), `CLAUDE_CODE_SHELL`, `CLAUDE_CODE_TMPDIR`, `USE_BUILTIN_RIPGREP`
- `CLAUDE_CODE_NEW_INIT=1` — multi-phase `/init`
- OTEL: `CLAUDE_CODE_ENABLE_TELEMETRY` + `OTEL_*` vars for metrics/logging export

## Model configuration

Aliases: `default` (revert), `best`, `fable`, `sonnet`, `opus`, `haiku`, `sonnet[1m]`/`opus[1m]` (1M context), `opusplan` (opus for planning → sonnet for execution). Full IDs: `claude-opus-5-5` etc. Resolution order per session: `--model` > `ANTHROPIC_MODEL` family > `model` setting > account default. Related keys: `effortLevel`, `modelSettings` (per-model effort), `fallbackModel` (comma chain for overload), `availableModels`/`deniedModels`/`enforceAvailableModels` (allowlist), `modelPicker`, `modelOverrides` (map IDs e.g. to Bedrock ARNs), `maxEffortLevel`, `alwaysThinkingEnabled`, `fastMode`, `autoCompactWindow`/`autoCompactEnabled`, `advisorModel`, `outputStyle`, `language`.

## High-value settings.json keys (selected from ~200)

- `permissions` — `.allow` `.ask` `.deny` `.defaultMode` `.additionalDirectories` `.disableBypassPermissionsMode` `.blockReadsOutsideWorkingDirectories` (see permissions.md)
- `hooks` — event → matcher → command (see hooks.md); `disableAllHooks`, `allowedHttpHookUrls`, `httpHookAllowedEnvVars`
- `env` — session env vars
- `statusLine` — `{type:"command", command:"..."}` custom status bar; `fileSuggestion` (own `@` completer); `fileCheckpointingEnabled` (`/rewind` snapshots)
- `apiKeyHelper` — command that prints credentials; `awsAuthRefresh`, `gcpAuthRefresh`, `awsCredentialExport`
- `autoMode` (+`.classifyAllShell`), `disableAutoMode`, `skipDangerousModePermissionPrompt`
- `sandbox.*` — Bash sandboxing (see permissions.md)
- `enabledPlugins`, `extraKnownMarketplaces`, `strictPluginOnlyCustomization`, `skillOverrides`, `disableBundledSkills`, `disableSkillShellExecution`
- `enableAllProjectMcpServers`, `enabledMcpjsonServers`, `disabledMcpjsonServers`, `allowedMcpServers`, `deniedMcpServers`
- `attribution.commit`/`.pr`/`.sessionUrl` (commit/PR trailer text), `includeGitInstructions`, `prUrlTemplate`
- `editorMode` (vim), `theme`, `tui`, `verbose`, `viewMode`, `keybindingFlavor` (dead), `vimInsertModeRemaps`, `defaultShell`, `preferredNotifChannel`, `respectGitignore`, `companyAnnouncements`
- `autoUpdatesChannel`, `minimumVersion`/`requiredMinimumVersion`/`requiredMaximumVersion`, `cleanupPeriodDays`
- `agent`, `teammateMode`, `worktree.*` (`baseRef`,`sparsePaths`,`symlinkDirectories`,`bgIsolation`), `plansDirectory`
- Enterprise/managed-only: `forceLoginMethod`, `forceLoginOrgUUID`, `allowManagedHooksOnly`, `allowManagedMcpServersOnly`, `policyHelper.*`, `managedSourcesBehavior`, `disableSideloadFlags`, `strictKnownMarketplaces`, `wslInheritsWindowsSettings`

Full key-by-key index: https://code.claude.com/docs/en/settings-reference

## Passing config via CLI

`--settings` (file path or inline JSON, overrides same keys for session), `--mcp-config` (+`--strict-mcp-config`), `--plugin-dir`/`--plugin-url`, `--agents`, `--add-dir`, `--allowedTools`/`--disallowedTools`, `--permission-mode`, `--model`, `--effort`. None of these are restored on `--resume`/`--continue` — re-pass them. See cli-usage.md.
