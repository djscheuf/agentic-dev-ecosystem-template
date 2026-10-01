# Flake devShells and `nix develop`

## What is a devShell?

A `devShell` is a flake output that defines a development environment. It is the modern, reproducible replacement for `shell.nix`. You enter it with `nix develop`.

## Minimal flake devShell

```nix
{
  description = "My project";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs = { self, nixpkgs }:
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};
    in
    {
      devShells.${system}.default = pkgs.mkShell {
        buildInputs = [ pkgs.jq pkgs.curl ];
      };
    };
}
```

Enter it:

```bash
nix develop
```

## Named devShells

```nix
{
  outputs = { self, nixpkgs }:
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};
    in
    {
      devShells.${system} = {
        default = pkgs.mkShell { buildInputs = [ pkgs.jq ]; };
        backend = pkgs.mkShell { buildInputs = [ pkgs.python3 ]; };
      };
    };
}
```

Use a named shell:

```bash
nix develop .#backend
```

## Multi-system devShells

Most projects should support multiple systems. Use `nixpkgs.lib.genAttrs` or `flake-utils`:

```nix
{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let pkgs = nixpkgs.legacyPackages.${system}; in
      {
        devShells.default = pkgs.mkShell {
          buildInputs = [ pkgs.jq pkgs.curl ];
        };
      });
}
```

## Running a command in a devShell without entering it

```bash
nix develop .#default --command make test
nix develop .#backend --command python3 manage.py runserver
```

## Combining devShells

If you have multiple project shells, you can compose them:

```nix
{
  outputs = { self, nixpkgs }:
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};
      common = pkgs.mkShell { buildInputs = [ pkgs.git ]; };
      backend = pkgs.mkShell { buildInputs = [ pkgs.python3 ]; };
    in
    {
      devShells.${system} = {
        default = common;
        full = pkgs.mkShell {
          inputsFrom = [ common backend ];
        };
      };
    };
}
```

## devShell with a project derivation

```nix
{
  outputs = { self, nixpkgs }:
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};
      myapp = pkgs.callPackage ./default.nix {};
    in
    {
      packages.${system}.default = myapp;
      devShells.${system}.default = pkgs.mkShell {
        inputsFrom = [ myapp ];
        buildInputs = [ pkgs.gnumake pkgs.gdb ];
      };
    };
}
```

## Best practices

- **Commit `flake.lock`** so the devShell is reproducible across machines.
- **Use `flake-utils` or `nixpkgs.lib.genAttrs`** to avoid duplicating per-system boilerplate.
- **Name devShells by purpose** (`default`, `backend`, `frontend`, `ci`) when a project has distinct environments.
- **Keep `buildInputs` minimal** — only include what the developer needs interactively; derivation inputs go in `default.nix`.
- **Use `shellHook` for lightweight setup** (environment variables, tool version checks), not for heavy builds.
- **Document how to enter the shell** in the project README: `nix develop` or `nix develop .#<name>`.
