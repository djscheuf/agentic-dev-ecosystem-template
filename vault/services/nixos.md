# NixOS development environment

This repository is developed on NixOS. Use `nix-shell` as the default way to provide missing terminal or command-line dependencies.

*Last confirmed: 2026-08-29.*

## Current environment

- OS: NixOS 25.11 (Xantusia)
- `nix-shell`: 2.31.3 at `/run/current-system/sw/bin/nix-shell`

## Implications for agents

- Prefer `nix-shell` over `apt`, `brew`, `npm -g`, or manual downloads when a command-line tool is missing.
- Check whether a tool is already available in `/run/current-system/sw/bin` before entering a new shell.
- The project Devin configuration already allows `Exec(nix-shell)`, so agents can invoke it without a permission prompt.
