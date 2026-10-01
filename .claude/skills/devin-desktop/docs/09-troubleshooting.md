# Troubleshooting

Scenario-based fixes for common Devin Desktop and Devin Local issues.

## Agent not available

- Check that the workspace is not in **Restricted Mode**. In Restricted Mode, all agents and hooks are disabled.
- For Devin Local, open Devin Settings > Agents and ensure **Devin Local** is toggled on, then restart.
- On Enterprise plans, confirm the admin has enabled the **Devin Local Agent** team setting.

## Devin Local does not appear in the agent selector

1. Open Devin Settings > Agents.
2. Toggle **Devin Local** on.
3. Restart Devin Desktop.
4. If on Enterprise, ask the admin to enable it in the team dashboard.

## Commands not auto-executing

### Cascade

- Check the auto-execution level in the bottom-right settings panel: `Disabled`, `Allowlist Only`, `Auto`, `Turbo`.
- Confirm the command is in `windsurf.cascadeCommandsAllowList` and not in `windsurf.cascadeCommandsDenyList`.
- For Teams/Enterprise, the admin may have set a maximum allowed level below `Turbo`.

### Devin Local

- Check `permissions` in `~/.config/devin/config.json` and `.devin/config.json`.
- Use `Allow` rules for commands you want auto-approved, `Ask` for prompts, `Deny` for blocks.
- Remember permission rules are merged across config levels; deny takes precedence.

## Hooks not running

- Verify the file path. Recommended: `.devin/hooks.v1.json`.
- Confirm the workspace is not in Restricted Mode.
- Run `/hooks` to see loaded hooks and their source.
- If loading from `.claude/` paths, ensure `read_config_from.claude` is not set to `false`.
- Check that the file is valid JSON.

## MCP not connecting

### Devin Local

- Ensure the server is defined under `mcpServers` in `.devin/config.json` or `~/.config/devin/config.json`.
- For `stdio`, check the `command` and `args` and that the binary is on PATH.
- For `http`, verify the `url` and `transport` (`http` or `sse`).
- Devin Local prompts for MCP tool approval by default. Approve the tool or the whole server, either for the session or permanently.

### Cascade

- Check `~/.codeium/windsurf/mcp_config.json`.
- HTTP servers may use `serverUrl` instead of `url`.
- Confirm the server is enabled in the MCP panel in Devin Desktop.

## Network and proxy issues

Devin CLI routes its outbound HTTPS traffic through a proxy when configured.

### Environment variables

```bash
export HTTPS_PROXY=http://proxy.corp.example.com:8080
export HTTP_PROXY=http://proxy.corp.example.com:8080
export ALL_PROXY=socks5://proxy.corp.example.com:1080
export NO_PROXY=localhost,127.0.0.1,.internal.corp
```

### Config file

```json
{
  "proxy": {
    "mode": "manual",
    "url": "http://proxy.corp.example.com:8080",
    "no_proxy": "localhost,127.0.0.1,.internal.corp"
  }
}
```

On macOS and Windows, `proxy.mode: "system"` also honors platform PAC settings.

## Debug logs

Raise log levels and mirror logs to the terminal:

```bash
RUST_LOG="chisel=trace,windsurf_api_client=trace,connect_rpc=trace,reqwest=trace,hyper=trace,hyper_util=trace,rustls=trace" \
  CHISEL_LOG_STDOUT=1 \
  devin auth login
```

Log files are also written to:

- macOS / Linux: `~/.local/share/devin/cli/logs/devin_<timestamp>_<pid>.log`
- Windows: `%APPDATA%\devin\cli\logs\devin_<timestamp>_<pid>.log`

Warning: trace logs may contain tokens and headers. Scrub before sharing.

## Authentication issues

- For remote or SSH sessions, use `devin auth login --force-manual-token-flow`.
- Log out and back in: `devin auth logout && devin auth login`.
- Check status: `devin auth status`.
- On Enterprise, confirm the account has Devin CLI/Desktop access in team settings.

## Dev Container issues

- Devin Desktop does not run dev container lifecycle commands (`onCreateCommand`, `postCreateCommand`, etc.).
- Use a feature `entrypoint` for setup that must run at container start.
- For remote dev containers over SSH, connect via Remote-SSH first, then run the dev container commands.

## SSH issues

- Only Linux remote hosts are supported.
- Do not install the Microsoft Remote-SSH or open-remote-ssh extensions; they conflict.
- Reload the window to refresh SSH agent forwarding.
- If on Windows, password prompts may appear in `cmd.exe` windows; this is expected.
