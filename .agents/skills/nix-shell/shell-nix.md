# Writing a shell.nix

## Default entry points

When you run `nix-shell` without arguments, it looks for:

1. `shell.nix` in the current directory
2. `default.nix` in the current directory

So `shell.nix` is the conventional place to define a project development environment.

## Minimal shell.nix

```nix
{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  buildInputs = [ pkgs.jq pkgs.curl ];
}
```

Enter it:

```bash
nix-shell
```

## mkShell attributes

| Attribute | Purpose |
|-----------|---------|
| `buildInputs` | Packages available at runtime/development time |
| `nativeBuildInputs` | Tools that run on the host during development (compilers, formatters) |
| `propagatedBuildInputs` | Dependencies propagated to consumers |
| `shellHook` | Shell commands run after the environment is set up |
| `inputsFrom` | Inherit build inputs from other derivations |
| `name` | Name of the shell (shown in prompt) |

Example with `shellHook`:

```nix
{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  buildInputs = [ pkgs.jq pkgs.nodejs ];
  shellHook = ''
    echo "Welcome to the project shell"
    export API_KEY=$(cat ~/.config/myapp/api-key)
  '';
}
```

## Using `inputsFrom`

If your project has a derivation, you can reuse its inputs:

```nix
{ pkgs ? import <nixpkgs> {} }:

let
  myProject = pkgs.callPackage ./default.nix {};
in
pkgs.mkShell {
  inputsFrom = [ myProject ];
  buildInputs = [ pkgs.gnumake pkgs.gdb ];
}
```

## Pinning nixpkgs in shell.nix

For reproducibility, pin nixpkgs rather than relying on `<nixpkgs>`:

```nix
let
  nixpkgs = builtins.fetchTarball {
    url = "https://github.com/NixOS/nixpkgs/archive/nixos-unstable.tar.gz";
    sha256 = "...";
  };
  pkgs = import nixpkgs {};
in
pkgs.mkShell {
  buildInputs = [ pkgs.jq ];
}
```

For new projects, prefer a flake-based `devShell` (see [devshells.md](./devshells.md)) so dependencies are tracked in `flake.lock`.

## Conditional packages by platform

```nix
{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  buildInputs = with pkgs; [
    jq
    curl
  ] ++ lib.optionals pkgs.stdenv.isLinux [
    inotify-tools
  ] ++ lib.optionals pkgs.stdenv.isDarwin [
    darwin.libiconv
  ];
}
```

## Passing arguments to shell.nix

```nix
{ pkgs ? import <nixpkgs> {}
, withDocs ? false
}:

pkgs.mkShell {
  buildInputs = [ pkgs.jq ] ++ pkgs.lib.optional withDocs pkgs.pandoc;
}
```

Invoke with an argument:

```bash
nix-shell --arg withDocs true
```

## Best practices

- **Keep `shell.nix` simple and project-specific**; do not try to replace the whole system configuration.
- **Pin `nixpkgs` or use a flake** so teammates get the same versions.
- **Use `nativeBuildInputs` for tools** like compilers and linters, `buildInputs` for libraries your project links against.
- **Use `shellHook` for project-specific setup** (e.g., environment variables, greeting messages), but avoid heavy logic.
- **Prefer `nix develop` in flake projects**; keep `shell.nix` for legacy or flake-less workflows.
