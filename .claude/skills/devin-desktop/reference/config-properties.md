# Config property reference

Devin Local and Devin CLI use JSON-with-comments config files. The same files are loaded by Devin Local in Devin Desktop.

## File precedence

From highest to lowest:

1. Organization / team settings
2. Session interactive approvals
3. `.devin/config.local.json` (gitignored)
4. `.devin/config.json` (committed)
5. `~/.config/devin/config.json` (user defaults)

On Windows, the user config is `%APPDATA%\devin\config.json`.

## Available at each level

| Setting | User config | Project config |
|---------|:-----------:|:--------------:|
| `permissions` | yes | yes |
| `mcpServers` | yes | yes |
| `read_config_from` | yes | yes |
| `hooks` | yes | yes |
| `agent` | yes | no |
| `theme_mode` | yes | no |
| `show_path` | yes | no |
| `unicode_mode` | yes | no |
| `show_hints` | yes | no |
| `include_gitignored_files` | yes | no |
| `respect_gitignore` | yes | no |
| `attribution` | yes | no |
| `auto_update` | yes | no |
| `notify` | yes | no |
| `proxy` | yes | no |
| `sandbox` | yes | no |

## User-only options

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `agent.model` | string | `swe-1-6-fast` | Default AI model. |
| `agent.show_history_on_continue` | boolean | `true` | Show previous messages when resuming a session. |
| `theme_mode` | string or null | `null` | `light`, `dark`, `terminal-dark`, `terminal-light`, `nocolor`, or `null` for auto. |
| `show_path` | boolean | `false` | Show current working directory in the input border. |
| `unicode_mode` | string | `auto` | `auto`, `unicode`, or `ascii`. |
| `show_hints` | boolean | `true` | Show tips between turns. |
| `include_gitignored_files` | boolean | `false` | Include gitignored files in `@` tab completion. |
| `respect_gitignore` | boolean | `false` | Block tool access to gitignored paths. |
| `attribution` | boolean | `true` | Add `Generated with Devin` / `Co-Authored-By` to commits and PRs. |
| `auto_update` | boolean | `true` | Install new versions in the background on macOS and Linux. |
| `notify` | string | `smart` | `never`, `smart`, or `always` for terminal notifications. |

## Permissions

Available in user and project config.

```json
{
  "permissions": {
    "allow": ["Read(**)", "Exec(git)"],
    "deny": ["Exec(sudo)"],
    "ask": ["Write(**/.env*)"]
  }
}
```

- `allow` rules auto-approve.
- `deny` rules block.
- `ask` rules prompt.
- Deny takes precedence over allow.
- Permission lists are merged across config levels.

## MCP servers

```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": { "GITHUB_PERSONAL_ACCESS_TOKEN": "<token>" }
    },
    "remote": {
      "url": "https://mcp.example.com/mcp",
      "transport": "http"
    }
  }
}
```

- `command` / `args` / `env` for `stdio`.
- `url` and optional `transport` (`http`, `sse`) for HTTP.
- Servers are merged by name across levels; a higher-priority server overrides a lower-priority one of the same name.

## read_config_from

Controls importing rules, skills, and MCP servers from other tools.

```json
{
  "read_config_from": {
    "agents_standard": true,
    "cursor": true,
    "windsurf": true,
    "claude": true,
    "opencode": true,
    "vscode": true,
    "zed": true
  }
}
```

| Option | Source |
|--------|--------|
| `agents_standard` | `AGENTS.md`, `AGENTS.local.md`, `AGENT.md`, `.windsurfrules` |
| `cursor` | `.cursor/rules/*.md`, `.cursor/rules/*.mdc`, `.cursor/mcp.json` |
| `windsurf` | `.windsurf/rules/*.md`, `.windsurf/global_rules.md`, `.windsurf/skills/`, `~/.codeium/<channel>/mcp_config.json` |
| `claude` | `CLAUDE.md`, `~/.claude/CLAUDE.md`, `.claude/skills/**/SKILL.md`, `.claude/commands/**/*.md`, various `.mcp.json` and settings files |
| `opencode` | `opencode.json`, `~/.config/opencode/opencode.json` |
| `vscode` | `.vscode/mcp.json` |
| `zed` | `.zed/settings.json`, `~/.config/zed/settings.json` |

All default to `true`. Set to `false` to disable.

## Proxy

User-only.

```json
{
  "proxy": {
    "mode": "system",
    "url": null,
    "no_proxy": null
  }
}
```

| Option | Type | Description |
|--------|------|-------------|
| `mode` | string | `system`, `manual`, or `off`. |
| `url` | string or null | Proxy URL; required when `mode` is `manual`. |
| `no_proxy` | string or null | Comma-separated bypass list. |

On macOS and Windows, `system` also honors platform PAC settings.

## Sandbox

User-only.

```json
{
  "sandbox": {
    "allowed_domains": [],
    "denied_domains": [],
    "network_mode": "full"
  }
}
```

| Option | Type | Description |
|--------|------|-------------|
| `allowed_domains` | array of strings | Domain allowlist. Empty means no filtering. |
| `denied_domains` | array of strings | Domain denylist. Takes precedence over allowed. |
| `network_mode` | string | `full` or `limited` (GET/HEAD/OPTIONS only). |
