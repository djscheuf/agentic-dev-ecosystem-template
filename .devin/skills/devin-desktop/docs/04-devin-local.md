# Devin Local agent

Devin Local is the default agent for new tabs in Devin Desktop. It shares the same harness as Devin CLI, so it uses the same modes, permissions, and configuration files.

## Switching to Devin Local

1. Open the Command Palette (`Cmd/Ctrl+Shift+P`) and run **Open Devin User Settings**.
2. Click the **Agents** tab.
3. Toggle **Devin Local** on.
4. Restart Devin Desktop.

You can also disable Cascade entirely with the `devin.cascade.enabled` setting. New tabs default to Devin Local when available, falling back to Cascade if Devin Local is not enabled or accessible.

## Modes

| Mode | Description |
|------|-------------|
| **Normal** | Standard agentic coding. |
| **Plan** | Read-only research and planning. Writes a plan to `~/.devin/plans/plan-<session>.md` and waits for approval. |
| **Ask** | Q&A without editing files. |

To enter a more thorough Plan mode, include `megaplan`, `ultraplan`, or `masterplan` in the prompt.

## Subagents

Devin Local can spawn subagents in the foreground or background. They share tools and codebase context but run in their own conversation chains.

- Enable with the **Subagents (Preview)** toggle in Devin Settings.
- Built-in profiles include **Quick Review** for rapid feedback on changes.
- Define custom subagents in `agents/<name>.md` (flat file) or `agents/<name>/AGENT.md` (directory). The identifier is the file or directory name.

## Worktree sessions

Run Devin Local in a git worktree to keep edits isolated from the main workspace.

- **New worktree:** Devin Desktop creates a fresh worktree for the session.
- **Existing worktree:** Pick one from the selector's **Local** submenu.
- Click **Merge** on the session to bring changes back into the main workspace.

## Permissions model

Devin Local replaces Cascade's auto-execution levels with fine-grained permissions.

| Rule type | Effect |
|-----------|--------|
| **Deny** | Blocks the action entirely. Highest priority. |
| **Ask** | Always prompts for approval. |
| **Allow** | Auto-approves the action. |

Permissions can be scoped to:

- `Read(path-glob)`
- `Write(path-glob)`
- `Exec(command-glob)`
- `Http(domain)`
- MCP tools

Rules use globs and are evaluated against every workspace directory, including directories added after the session starts.

When the agent requests permission, you can:

- Edit the command inline.
- Use keyboard shortcuts shown on the request card.
- Grant session-wide approval so the same scope is not re-prompted.

## Sandboxing

When enabled, the sandbox enforces filesystem isolation and network filtering.

- Writable paths come from permission scopes.
- `Read(...)` deny rules hide paths from sandboxed commands.
- `sandbox.allowed_domains` and `sandbox.denied_domains` control network access.
- Enterprise admins can require sandbox mode and set organization-wide domain rules in team settings.

## Customizations

Open the **Customizations** surface to see everything a Devin Local session has loaded: rules, skills, hooks, MCP servers, and plugins. Access it from the new-tab menu in an agent space or by right-clicking a Devin Local session in the agent sidebar.

Note: **Plugins** in this context are Devin agent plugins (skills, rules, hooks, MCP, subagents). They are not the same as editor extensions installed from the Open VSX marketplace.

## Enterprise gating

Devin Local is controlled by the **Devin Local Agent** team setting. On non-enterprise plans it is available by default unless a member's access is disabled. On Enterprise plans an admin must enable it.

- Devin Enterprise: `app.devin.ai/org/{orgName}/settings/windsurf` under **Features**.
- Windsurf Enterprise: the Windsurf team dashboard.

Restart Devin Desktop after the team setting is changed.
