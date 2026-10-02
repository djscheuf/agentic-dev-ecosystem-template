---
description: Reference for using, configuring, and scripting the Claude Code CLI — flags, settings, hooks, permissions, skills/MCP extensibility, headless mode, and debugging. Consult for any task involving the `claude` command, .claude/ config, or wrapping Claude Code in scripts/agents.
---

# Claude Code

Anthropic's agentic CLI (`claude`): an interactive terminal agent that reads, writes, and runs code in a loop — model proposes, tools execute, results feed back — until the task is done. Same binary powers interactive sessions, headless `claude -p` runs, the Agent SDK, Desktop, and cloud sessions, so configuration and debugging techniques transfer across surfaces.

Quick mental model:
- **Prompt** goes in (terminal, flag, stdin, or SDK call); **agent loop** iterates tool calls; **result** comes out
- **Config** layers: managed → local → project → user settings.json, env vars, CLI flags (see configuration.md for precedence)
- **Context** fills from CLAUDE.md, `.claude/` skills/agents/rules, `.mcp.json` servers, system prompt — `--bare` skips all of it, `--safe-mode` skips customizations but keeps auth/permissions
- **Permissions** gate every tool call via rules + mode + prompt fallback; hooks can observe/block/rewrite at each lifecycle point

Common one-liners:
```bash
claude                                    # interactive session
claude -p "task" --output-format json     # one-shot scripted run
claude -c / claude -r <id>                # continue / resume a session
claude doctor                             # diagnose install & settings
```

## Reference files

- `ref/cli-usage.md` — commands & flags, interactive session controls (slash commands, vim/editor modes, Plan mode, background tasks), session lifecycle, keybindings. Consult for how to drive `claude` day-to-day.
- `ref/configuration.md` — settings.json files & precedence, all key settings, env vars, `~/.claude` directory layout, CLAUDE.md/memory mechanics, model selection, `--settings`/`--setting-sources` for passing config on the CLI. Consult for anything about where config lives or why a value applies.
- `ref/hooks.md` — every hook event, matcher syntax, JSON stdin contract, exit codes & control fields, prompt/agent/HTTP hook types, hook security model. Consult when writing or debugging hooks.
- `ref/permissions.md` — permission rule syntax, modes (Manual/auto/dontAsk/acceptEdits/plan), what each built-in tool can do, sandboxed Bash, workspace trust. Consult when a call prompts/gets denied or when writing allow/deny rules.
- `ref/extending.md` — skills, subagents, MCP servers, plugins: frontmatter schemas, scopes, transports, approval flows, mechanism-selection guide. Consult when adding capabilities or packaging for a team.
- `ref/headless-and-sdk.md` — `claude -p` print mode, output formats & stream-json event model, `--bare`, unattended permission strategies, process lifecycle signals, Agent SDK overview. Consult when scripting or wrapping Claude Code.
- `ref/debugging.md` — `/context`, `/doctor`, `/debug`, safe-mode & clean-config isolation, common failure patterns (hooks not firing, MCP down, settings ignored), error-message map, performance fixes. Consult first when something's wrong.

Out of scope (not covered here): claude.ai web/desktop/mobile apps, IDE extensions, enterprise deployment & managed policy details, Remote Control, and the raw Claude API (that's platform.claude.com).

Source: https://code.claude.com/docs — full page index at https://code.claude.com/docs/llms.txt
