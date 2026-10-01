# Troubleshooting nix-shell

## Command not found

If you see `command not found` on NixOS:

1. Determine if the missing command is a core utility (`ls`, `cat`, `grep`, `sed`, `awk`, `sh`). If yes, the system PATH is broken or the command is misspelled.
2. Otherwise, find the package and use `nix-shell`:

   ```bash
   nix-shell -p <package> --run "<command>"
   ```

## Package not found

If `nix-shell -p <name>` fails with an attribute error:

1. Search the exact attribute: https://search.nixos.org/packages.
2. Try `nix search nixpkgs <term>`.
3. For Python libraries, use `python3Packages.<name>`.
4. For tools with different names, check the package's `pname` or `meta.description`.

## nix-shell vs nix shell confusion

- `nix-shell -p <pkg>` is the legacy CLI and works even without flakes.
- `nix shell nixpkgs#<pkg>` requires flakes and the `nix-command` experimental feature.

If `nix shell` is unavailable, use `nix-shell -p`.

## Environment is wrong inside `--run`

`--run` executes in a non-interactive shell. If your shell startup files (e.g., `.bashrc`) are doing something unexpected, use `--command` or check whether the issue is from the shell environment, not Nix.

## `--pure` cleared too much

If `--pure` removes variables you need (e.g., `SSH_AUTH_SOCK`, `EDITOR`, `TERM`), keep them explicitly:

```bash
nix-shell -p <pkg> --pure --keep SSH_AUTH_SOCK --keep EDITOR --run "<cmd>"
```

## Python packages are not importable

Make sure you are using the Python interpreter that comes with the nix-shell environment, not the one from the system:

```bash
nix-shell -p python3Packages.openpyxl --run "which python3 && python3 -c 'import openpyxl'"
```

If `which python3` points outside `/nix/store`, your shell is not using the nix-shell environment.

## Common anti-patterns

### Don't: give up and use an inferior tool

```bash
python3 script.py          # fails
libreoffice --convert-to csv file.xlsx   # loses data
```

### Do: use the right tool via nix-shell

```bash
nix-shell -p python3Packages.openpyxl --run "python3 -c '...'"
```

### Don't: install globally for one-off tasks

```bash
nix-env -iA nixpkgs.python3
```

### Do: use nix-shell temporarily

```bash
nix-shell -p python3 --run "python3 script.py"
```

### Don't: use bare Python library names

```bash
nix-shell -p openpyxl   # usually fails
```

### Do: use the full attribute path

```bash
nix-shell -p python3Packages.openpyxl
```

## Agentic checklist

When a tool is missing while you are automating a task on NixOS:

1. **Recognize it is NixOS** — global installation is not the default.
2. **Search for the package** with `nix search nixpkgs <tool>` or `search.nixos.org`.
3. **Use `nix-shell -p <pkg> --run "<cmd>"`** for one-off commands.
4. **Combine all needed packages** in a single `nix-shell` call.
5. **Preserve data integrity** — don't convert formats unnecessarily.
6. **For recurring work**, create a `shell.nix` or flake `devShell`.
