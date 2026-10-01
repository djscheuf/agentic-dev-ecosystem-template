---
name: nix-shell
description: "Use this skill for any task involving nix-shell, nix develop, development environments, temporary shells, or one-off package access on a Nix/NixOS system. Triggers include: nix-shell, nix develop, shell.nix, devShell, development environment, temporary shell, one-off package, shebang scripts, or 'command not found' on NixOS. Link out to the nix skill for Nix language and flake details, and to the nixos skill for system-level configuration."
---

# nix-shell Skill

## Overview

`nix-shell` builds a temporary environment containing the packages and dependencies you specify, then drops you into a shell (or runs a command). It is the standard way to access tools on NixOS without permanently installing them, and the standard way to set up reproducible project environments on any Nix system.

Use this skill when you are:

- Running a command and getting `command not found` on NixOS.
- Creating a reproducible development environment for a project.
- Writing a `shell.nix` or `flake.nix` `devShell`.
- Writing a script with a `nix-shell` shebang.
- Deciding whether to use `nix-shell`, `nix shell`, or `nix develop`.

## `nix-shell` vs `nix shell` vs `nix develop`

| Command | When to use it |
|---------|----------------|
| `nix-shell -p <pkg>` | Quick, temporary access to one or more packages (legacy CLI) |
| `nix-shell` | Use `shell.nix` / `default.nix` in the current directory (legacy CLI) |
| `nix shell <flake>` | Modern replacement for `nix-shell -p`, uses flakes |
| `nix develop <flake>` | Enter a flake `devShell` (modern, project-oriented) |

On NixOS, `nix-shell -p` is universally available and the fastest way to get a tool for a single command. `nix develop` is preferred inside flake-based projects.

## Decision tree: when to use nix-shell

```
Command fails with "command not found"
    ↓
Is it a core utility (ls, cat, grep, sed, awk, sh)?
    YES → Something is wrong with the system or PATH
    NO  → Use nix-shell
        ↓
    Do you know the package name?
        YES → nix-shell -p <package> --run "<command>"
        NO  → Search with nix search nixpkgs <term> or https://search.nixos.org
              Then try nix-shell -p <package> --run "<command>"
```

## Quick reference

| Task | Command |
|------|---------|
| Run one command with a package | `nix-shell -p <pkg> --run "<cmd>"` |
| Run with multiple packages | `nix-shell -p <pkg1> <pkg2> --run "<cmd>"` |
| Interactive shell with packages | `nix-shell -p <pkg1> <pkg2>` |
| Use a project shell.nix | `nix-shell` |
| Enter a flake devShell | `nix develop` |
| Run a command in a flake devShell | `nix develop .#default --command <cmd>` |
| Clean environment (close to build) | `nix-shell -p <pkg> --pure --keep HOME` |
| Self-contained script | `#!/usr/bin/env nix-shell` (see shebangs guide) |

## Progressive disclosure

Start with the guide that matches your task:

- **[Basic usage patterns](./basic-patterns.md)** — `-p`, `--run`, `--command`, `--pure`, interactive shells.
- **[shell.nix and mkShell](./shell-nix.md)** — how to write a reusable `shell.nix`.
- **[Flake devShells and nix develop](./devshells.md)** — modern, reproducible project environments.
- **[Shebang scripts](./shebangs.md)** — scripts that carry their own dependencies.
- **[Package discovery](./package-discovery.md)** — how to find the right package or attribute name.
- **[Common environments and examples](./common-envs.md)** — Python, Node, Rust, Excel parsing, and more.
- **[Troubleshooting](./troubleshooting.md)** — common errors, environment issues, and anti-patterns.

## Core NixOS principle

On NixOS, most tools are not globally installed. This is a feature, not a bug. Use `nix-shell` to access the entire Nix package ecosystem temporarily, without cluttering your system.

## When to delegate to other skills

- If you are configuring a whole NixOS system or service → switch to the [`nixos`](../nixos/SKILL.md) skill.
- If you need to understand Nix language syntax, flakes, or the Nix store → switch to the [`nix`](../nix/SKILL.md) skill.

## Remember

- **Preserve data integrity**: don't convert Excel to CSV if you need sheets, formulas, or formatting. Use `nix-shell -p python3Packages.openpyxl` instead.
- **Combine tools in one shell**: `nix-shell -p python3Packages.pandas python3Packages.openpyxl --run ...`
- **Don't install globally with `nix-env` for a one-off task**: use `nix-shell` or `nix run` instead.
