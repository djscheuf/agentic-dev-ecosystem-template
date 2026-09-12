---
name: devin-desktop
description: Reference for configuring and debugging Devin Desktop, Devin Local, and the shared Devin CLI harness. Use for install, settings, hooks, MCP, permissions, and troubleshooting.
---

# Devin Desktop

Use this skill when a task touches Devin Desktop, Devin Local, Cascade, `.devin/` configuration, hooks, MCP, or agentic-workflow setup.

## Mental model

- Devin Desktop is a VS Code-fork IDE with an integrated AI agent panel.
- It runs two agent back-ends: **Devin Local** (default, shared with Devin CLI) and the legacy **Cascade**.
- Devin Local uses the same files as Devin CLI: `~/.config/devin/config.json`, `.devin/config.json`, `.devin/config.local.json`, `.devin/hooks.v1.json`, `.devin/skills/`, `AGENTS.md`.
- Cascade is legacy and uses a separate set of files: `~/.codeium/windsurf/mcp_config.json`, `.windsurf/rules/`, `.windsurf/workflows/`, `~/.codeium/windsurf/memories/`.

## Quick navigation

- [Overview](docs/01-overview.md)
- [Install and onboarding](docs/02-install-onboard.md)
- [Devin Desktop settings](docs/03-settings.md)
- [Devin Local agent](docs/04-devin-local.md)
- [Cascade features](docs/05-cascade.md)
- [Terminal and command execution](docs/06-terminal.md)
- [Extensibility: MCP, rules, skills, plugins](docs/07-extensibility.md)
- [Hooks](docs/08-hooks.md)
- [Troubleshooting scenarios](docs/09-troubleshooting.md)
- [Config property reference](reference/config-properties.md)
- [Hook event reference](reference/hook-events.md)
- [Settings keymap](reference/settings-keymap.md)

## When to run this skill

- Installing or updating Devin Desktop.
- Configuring Devin Local or Cascade.
- Writing or debugging `.devin/config.json`, `.devin/hooks.v1.json`, `.devin/skills/`, or `AGENTS.md`.
- Setting up MCP servers, rules, or skills.
- Diagnosing agent, terminal, or permission issues.

## Quick start

1. Install Devin Desktop for your platform.
2. Log in and enable the Devin Local agent in Devin Settings.
3. Add project context via `AGENTS.md` or `.devin/rules/`.
4. Configure shared tooling in `.devin/config.json` (permissions, MCP, hooks).
5. Use `devin` from the terminal or open a folder with `devin-desktop <path>`.
