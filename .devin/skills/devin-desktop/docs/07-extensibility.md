# Extensibility

Devin Desktop and Devin Local can be extended with rules, skills, MCP servers, and plugins.

## Rules

Rules provide always-on or conditionally-active context.

- **Devin Local / CLI:** prefers `.devin/rules/*.md` and `AGENTS.md`. Legacy `.windsurf/rules/` is still read.
- **Cascade:** uses `.windsurf/rules/*.md` and `~/.codeium/windsurf/memories/global_rules.md`.
- `AGENTS.md` at the workspace root is always on; `AGENTS.md` in subdirectories is applied when the active file is in that directory.

## Skills

Skills are reusable procedures committed as `SKILL.md` files.

- Devin Local discovers skills from `.devin/skills/` (project) and `~/.config/devin/skills/` (user).
- Invoke a skill by name or let the model call it automatically.
- For Cascade, skills are also available and the model can invoke them dynamically or via `@mention`.

## Workflows (Cascade only)

Workflows are manual prompt templates in `.windsurf/workflows/*.md` and `~/.codeium/windsurf/global_workflows/*.md`. They are not supported by Devin Local; migrate them to skills.

## MCP

MCP servers add custom tools to the agent.

### Devin Local / CLI

Define servers in `.devin/config.json` or `~/.config/devin/config.json` under `mcpServers`:

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

- `stdio` transport: `command`, `args`, `env`.
- `http` transport: `url`, plus `transport` (`http` or `sse`), headers, and optional OAuth.
- Devin Local prompts for approval before each MCP tool call by default.

### Cascade

Cascade uses `~/.codeium/windsurf/mcp_config.json` with the same `mcpServers` shape. It also supports `serverUrl` for HTTP servers and config interpolation.

## Plugins

Devin agent plugins are installable bundles that contribute skills, rules, hooks, MCP servers, and subagents. They are managed in the agent's **Customizations** surface and are not the same as editor IDE extensions from the Open VSX marketplace.
