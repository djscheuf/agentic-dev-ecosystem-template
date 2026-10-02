# Finding packages and attributes for nix-shell

## Method 1: try the obvious name

Many packages are available under their project name:

```bash
nix-shell -p python3
nix-shell -p nodejs
nix-shell -p jq
nix-shell -p git
nix-shell -p pandoc
```

This works often enough that it is worth trying first.

## Method 2: search the web index

https://search.nixos.org/packages is the most reliable way to find the exact attribute path and available versions. It shows:

- The attribute name (e.g., `python3Packages.openpyxl`).
- The package name.
- The Nixpkgs channel it belongs to.
- License and platform information.

## Method 3: search with the Nix CLI

With flakes enabled:

```bash
nix search nixpkgs <term>
nix search nixpkgs openpyxl
nix search nixpkgs 'python3Packages.openpyxl'
```

The legacy `nix-env` search:

```bash
nix-env -qaP '.*openpyxl.*'
nix-env -qaP 'python3.*' | grep openpyxl
```

`-qaP` queries available packages with attribute paths. The first column is the attribute path (e.g., `nixpkgs.python3Packages.openpyxl`), which is what you use with `-p`:

```bash
nix-shell -p python3Packages.openpyxl
```

## Method 4: grep nixpkgs locally

If you have a local nixpkgs checkout:

```bash
grep -R "openpyxl" /path/to/nixpkgs/pkgs/development/python-modules/
```

This is useful when you need to understand how a package is defined or what variants exist.

## Python package names

Python packages in Nixpkgs are usually under `python3Packages` or `python311Packages` (or similar):

```bash
nix-shell -p python3Packages.openpyxl
nix-shell -p python3Packages.pandas
nix-shell -p python3Packages.requests
nix-shell -p python3Packages.matplotlib
```

Do **not** use `nix-shell -p openpyxl` for Python libraries; it usually fails because the top-level package name may be different or unavailable.

## Node, Rust, Haskell, and other ecosystems

| Ecosystem | Attribute prefix | Example |
|-----------|------------------|---------|
| Node.js | `nodejs`, `nodePackages` | `nix-shell -p nodejs` |
| Rust | `cargo`, `rustc`, `rustPlatform` | `nix-shell -p cargo rustc` |
| Haskell | `haskellPackages` | `nix-shell -p haskellPackages.ghc` |
| Perl | `perlPackages` | `nix-shell -p perlPackages.LWP` |
| Ruby | `rubyPackages` | `nix-shell -p rubyPackages.rails` |
| Go | `go` | `nix-shell -p go` |

## Finding NixOS options

If you are configuring NixOS and need a service option, use:

- https://search.nixos.org/options
- `nixos-option <option>` (on a NixOS system)
- `nixos-help` for the manual

## Inspecting a package's attributes

Once you know an attribute name, inspect it:

```bash
nix eval nixpkgs#jq.meta.description
nix eval nixpkgs#jq.meta.homepage
nix eval nixpkgs#jq.pname
nix eval nixpkgs#jq.version
```

## Best practices

- **Start with `search.nixos.org`** for the most accurate attribute paths.
- **For Python, always use `python3Packages.<name>`**, not the bare package name.
- **Use `nix search nixpkgs <term>` for quick CLI searches** when flakes are enabled.
- **Check the package meta** (`nix eval nixpkgs#<pkg>.meta`) for description, license, and homepage if unsure.
- **Prefer exact attribute names** in scripts and `shell.nix` files to avoid ambiguous matches.
