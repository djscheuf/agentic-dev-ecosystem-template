# nix-shell shebang scripts

You can use `nix-shell` as a script interpreter so a script declares its own dependencies. This is useful for sharing small, self-contained scripts that run on any system with Nix installed.

## Basic syntax

Use two shebang lines:

```python
#! /usr/bin/env nix-shell
#! nix-shell -i python3 --packages python3 python3Packages.prettytable

import prettytable

t = prettytable.PrettyTable(["N", "N^2"])
for n in range(1, 10):
    t.add_row([n, n * n])
print(t)
```

Why two lines? Many operating systems only allow one argument in a `#!` line, so `#!/usr/bin/env nix-shell -i python3 ...` would not work reliably.

## How it works

1. `env nix-shell` starts `nix-shell`.
2. The second `#! nix-shell ...` line is parsed as options by `nix-shell`.
3. `nix-shell` installs the listed packages and invokes the interpreter given by `-i`.
4. The rest of the file is passed to that interpreter.

## `-i` interpreter

The `-i` flag specifies the real interpreter that will run the script. Examples:

| Language | Interpreter |
|----------|-------------|
| Python | `python3` |
| Bash | `bash` |
| Perl | `perl` |
| Haskell | `runghc` |
| Ruby | `ruby` |
| Node | `node` |

## Multiple `-p` lines

You can split packages across multiple shebang lines for readability:

```perl
#! /usr/bin/env nix-shell
#! nix-shell -i perl
#! nix-shell --packages perl
#! nix-shell --packages perlPackages.HTMLTokeParserSimple
#! nix-shell --packages perlPackages.LWP
#! nix-shell --packages perlPackages.LWPProtocolHttps

use HTML::TokeParser::Simple;
# ...
```

## Customizing packages with Nix expressions

You can pass a simple Nix expression as a package argument. Quote it to protect it from shell expansion:

```bash
#! /usr/bin/env nix-shell
#! nix-shell -i bash --packages 'terraform.withPlugins (plugins: [ plugins.openstack ])'

terraform apply
```

## Pinning nixpkgs in a shebang

You can pin a specific Nixpkgs revision with `-I`:

```haskell
#! /usr/bin/env nix-shell
#! nix-shell -i runghc --packages 'haskellPackages.ghcWithPackages (ps: [ps.download-curl ps.tagsoup])'
#! nix-shell -I nixpkgs=https://github.com/NixOS/nixpkgs/archive/nixos-20.03.tar.gz

import Network.Curl.Download
import Text.HTML.TagSoup
-- ...
```

## Best practices

- **Always use two shebang lines**: `#!/usr/bin/env nix-shell` followed by `#! nix-shell ...`.
- **Quote Nix expressions** in `-p` arguments to avoid shell parsing issues.
- **Keep scripts focused** — shebangs are great for small utilities, not large applications.
- **Consider a flake + `nix run`** for more complex scripts that need a lock file.
- **Make scripts executable**:

  ```bash
  chmod +x script.py
  ./script.py
  ```
