# Devin Desktop settings

Open Devin Settings from the top-right dropdown or with the Command Palette (`Cmd/Ctrl+Shift+P`) by running **Open Devin User Settings**.

## Commonly configured settings

| Setting | Where / key | What it does |
|---------|-------------|--------------|
| Devin Local agent | Settings > Agents | Toggle to enable or disable the Devin Local agent. Requires restart. |
| Cascade agent | `devin.cascade.enabled` | Toggle to enable or disable Cascade. |
| Subagents (Preview) | Settings > Agents | Allow Devin Local to spawn subagents. |
| Agent diff zones | Settings > User Interface | Show inline accept/reject controls for non-Cascade edits. |
| Cascade gitignore access | Settings > Cascade Gitignore Access | Allow agents to read files matched by `.gitignore`. Off by default. |
| Auto-execution level | Bottom-right status bar / Settings | How Cascade auto-runs terminal commands: `Disabled`, `Allowlist Only`, `Auto`, `Turbo`. |
| Command allow list | `windsurf.cascadeCommandsAllowList` | Commands always auto-executed by Cascade. |
| Command deny list | `windsurf.cascadeCommandsDenyList` | Commands that always require approval. |
| Extension marketplace URL | Settings > General | Change the Open VSX marketplace endpoint. |
| Legacy terminal profile | Settings > Terminal | Revert to the legacy terminal if the dedicated terminal has issues. |

## Agent diff zones

Diff zones are inline highlighted regions that show exactly what an agent changed, with per-hunk accept and reject controls. All agents use diff zones by default. Disable them for non-Cascade agents in Devin Settings > User Interface > **Agent Diff Zones**.

## SSH, Dev Containers, and WSL

| Feature | Location | Notes |
|---------|----------|-------|
| Remote-SSH | Command Palette `Remote-SSH` or `Open a Remote Window` | Requires OpenSSH. Linux hosts only. Conflicts with the Microsoft Remote-SSH extension. |
| Dev Containers | Command Palette `Dev Containers: ...` | Requires Docker. Does not run `onCreateCommand`, `postCreateCommand`, etc. Feature `entrypoint` is a workaround. |
| WSL | `Remote-WSL` in Command Palette | Beta. Requires WSL already set up. |

## Extension marketplace

Devin Desktop uses the Open VSX Registry. The default marketplace URL can be changed in Devin Settings under the General section. Recommended editor extensions are listed in the recommended plugins documentation.
