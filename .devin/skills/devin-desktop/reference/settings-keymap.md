# Settings and keymap

## Settings keys

| Setting | Key / path | Values / effect |
|---------|------------|-----------------|
| Devin Local enabled | Devin Settings > Agents | Toggle. Requires restart. |
| Cascade enabled | `devin.cascade.enabled` | Boolean. |
| Subagents (Preview) | Devin Settings > Agents | Boolean. |
| Agent diff zones | Devin Settings > User Interface | Boolean. |
| Cascade gitignore access | Devin Settings > Cascade Gitignore Access | Boolean. |
| Auto-execution level | Bottom-right status bar / Settings | `Disabled`, `Allowlist Only`, `Auto`, `Turbo`. |
| Cascade allow list | `windsurf.cascadeCommandsAllowList` | Array of command strings. |
| Cascade deny list | `windsurf.cascadeCommandsDenyList` | Array of command strings. |
| Legacy terminal | Settings > Terminal | Boolean. |
| Marketplace URL | Devin Settings > General | Open VSX endpoint URL. |

## Keyboard shortcuts

| Shortcut | Action |
|----------|--------|
| `Cmd/Ctrl+Shift+P` | Command Palette. |
| `Cmd/Ctrl+I` | Command mode in terminal. |
| `Cmd/Ctrl+L` | Send terminal selection to agent. |

## File paths

| File | Purpose |
|------|---------|
| `~/.config/devin/config.json` | Devin Local / CLI user config. |
| `.devin/config.json` | Project config (committed). |
| `.devin/config.local.json` | Project local overrides. |
| `.devin/hooks.v1.json` | Recommended hooks file. |
| `AGENTS.md` | Always-on or directory-scoped rules. |
| `~/.codeium/windsurf/mcp_config.json` | Cascade MCP config. |
| `~/.codeium/windsurf/memories/` | Cascade auto-generated memories. |
| `~/.codeium/windsurf/memories/global_rules.md` | Cascade global rules. |
| `.windsurf/rules/*.md` | Cascade workspace rules. |
| `.windsurf/workflows/*.md` | Cascade workflows. |
| `~/.codeium/windsurf/global_workflows/*.md` | Cascade global workflows. |

## Useful slash commands

| Command | Purpose |
|---------|---------|
| `/hooks` | List loaded hooks and sources. |
| `/model` | Switch the active model. |
| `/plan` | Enter Plan mode. |
| `/normal` | Enter Normal mode. |
| `/ask` | Enter Ask mode. |
