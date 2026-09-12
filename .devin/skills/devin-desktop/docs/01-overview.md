# Devin Desktop overview

Devin Desktop is a next-generation AI IDE. It is a fork of VS Code with an agentic coding assistant integrated directly into the editor.

## Agents

| Agent | What it is | Default? | Config files |
|-------|------------|----------|--------------|
| **Devin Local** | Local agent harness shared with Devin CLI. Operates on your machine with your files and tools. | Yes, for new tabs | `.devin/`, `~/.config/devin/`, `AGENTS.md` |
| **Cascade** | Legacy agent. Uses an older configuration model and is being superseded by Devin Local. | No | `~/.codeium/windsurf/`, `.windsurf/` |

## Key concepts

- **Modes:** Devin Local supports `Normal`, `Plan`, and `Ask` modes. Plan mode produces a persistent markdown plan at `~/.devin/plans/plan-<session>.md` before writing code. Add `megaplan`, `ultraplan`, or `masterplan` to a prompt to enter a more thorough Plan mode.
- **Permissions:** Devin Local uses `allow`, `ask`, and `deny` rules scoped to `Read`, `Write`, `Exec`, `Http`, and MCP tools. Cascade uses auto-execution levels (`Disabled`, `Allowlist Only`, `Auto`, `Turbo`).
- **Worktrees:** Devin Local can run in a git worktree so the agent edits, builds, and tests without touching the main workspace. Merge the worktree when done.
- **Subagents:** Devin Local can spawn independent subagents to handle subtasks. Enable the **Subagents (Preview)** toggle in Devin Settings. Define custom subagents in `agents/<name>.md` or `agents/<name>/AGENT.md`.
- **Sandboxing:** Devin Local can run in an OS-level sandbox with filesystem isolation and network filtering. Configure `allowed_domains` and `denied_domains` in the `sandbox` section of the config.
- **Restricted Mode:** In a Restricted Mode workspace, all agents are disabled and hooks do not load or run.

## Context engine

Devin Desktop indexes the open workspace and uses retrieval-augmented generation (RAG) to surface relevant code snippets as you write, ask questions, or invoke commands. Pro plans add larger context limits and custom context. Teams and Enterprise can also index remote repositories.
