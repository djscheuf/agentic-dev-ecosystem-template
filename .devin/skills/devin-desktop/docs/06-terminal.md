# Terminal

Devin Desktop includes an enhanced terminal with agent integration, natural-language command generation, and auto-execution controls.

## Commands in the terminal

- **Command mode:** Press `Cmd/Ctrl+I` in the terminal to describe what you want and generate the CLI syntax.
- **Send selection to agent:** Highlight text and press `Cmd/Ctrl+L` to send it to the agent panel.
- **@-mention terminals:** Reference an active terminal in the agent chat.

## Auto-execution levels for Cascade

| Level | Behavior |
|-------|----------|
| **Disabled** | All commands require manual approval. |
| **Allowlist Only** | Only commands matching the allow list auto-execute. |
| **Auto** | The agent judges whether a command is safe. Potentially risky commands still ask. Requires a premium model. |
| **Turbo** | All commands auto-execute except those in the deny list. |

Select the level from the bottom-right settings panel. For Teams and Enterprise, admins can set the maximum allowed level in the admin portal.

## Allow and deny lists

- **Allow list:** Commands always auto-executed when auto-execution is enabled. Setting: `windsurf.cascadeCommandsAllowList`.
- **Deny list:** Commands that always require approval. Setting: `windsurf.cascadeCommandsDenyList`.
- Team and user lists are merged. The deny list takes precedence over the allow list.

## Devin Local permissions

Devin Local does not use auto-execution levels. Instead it uses the permission rules in `~/.config/devin/config.json` and `.devin/config.json`. See [Devin Local](04-devin-local.md) and the [config reference](../reference/config-properties.md).

## Dedicated terminal

On macOS, Devin Desktop can use a dedicated terminal for the agent.

- Always uses `zsh`.
- Loads `.zshrc` and zsh-specific configuration.
- If you use another shell, create a shared configuration file that both shells can source.
- To disable, enable the **Legacy Terminal Profile** option in Devin Desktop settings.
