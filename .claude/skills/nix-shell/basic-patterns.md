# Basic nix-shell usage patterns

## Single command with one package

```bash
nix-shell -p <package> --run "<command>"
```

Example:

```bash
nix-shell -p jq --run "jq '.key' file.json"
```

## Single command with multiple packages

```bash
nix-shell -p <pkg1> <pkg2> --run "<command>"
```

Example:

```bash
nix-shell -p python3 python3Packages.requests --run "python3 fetch.py"
```

## Interactive shell

```bash
nix-shell -p <pkg1> <pkg2>
# now you are in a shell with those packages available
# exit with 'exit' or Ctrl-D
```

## Chaining multiple commands

```bash
nix-shell -p <packages> --run "command1 && command2 && command3"
```

## `--run` vs `--command`

| Flag | Behavior |
|------|----------|
| `--run cmd` | Runs `cmd` in a non-interactive shell and exits. Use for scripts and automation. |
| `--command cmd` | Runs `cmd` in an interactive shell. Implicit `exit` is added, so the shell exits after `cmd`. Add `return` at the end to stay interactive. |

Use `--run` for automation; use `--command` when you want to do additional setup and then drop into a shell.

## `--pure`

`--pure` clears almost all environment variables before starting the shell, giving you an environment closer to a real Nix build. A few variables are kept by default: `HOME`, `USER`, `DISPLAY`.

```bash
nix-shell -p <pkg> --pure --run "<cmd>"
```

Keep extra variables with `--keep`:

```bash
nix-shell -p <pkg> --pure --keep SSH_AUTH_SOCK --run "<cmd>"
```

## `--packages` vs `-p`

`-p` is a short alias for `--packages`. They are identical.

```bash
nix-shell --packages jq --run "jq '.' file.json"
nix-shell -p jq --run "jq '.' file.json"
```

## Full Nix expressions with `-p`

The `-p` arguments are interpreted as Nix expressions valid inside a `buildInputs` list, so you can pass overrides:

```bash
nix-shell -p 'git.override { withManual = false; }' --run "git --version"
```

## Pinning nixpkgs with `-I`

Override the `nixpkgs` used by `-p`:

```bash
nix-shell -p pan -I nixpkgs=https://github.com/NixOS/nixpkgs/archive/8a3eea054838b55aca962c3fbde9c83c102b8bf2.tar.gz --run "pan --version"
```

## Using `nix shell` (modern equivalent)

```bash
nix shell nixpkgs#jq -c jq '.key' file.json
nix shell nixpkgs#python3 nixpkgs#python3Packages.requests -c python3 fetch.py
```

Everything after `-c` is passed to the command. `nix shell` requires flakes.

## Common tool mappings

On NixOS, if you need a common tool and it is missing, use the corresponding package name:

| Need | Package | Example |
|------|---------|---------|
| Python 3 | `python3` | `nix-shell -p python3 --run "python3 script.py"` |
| Python + openpyxl | `python3Packages.openpyxl` | `nix-shell -p python3Packages.openpyxl --run "python3 -c '...'"` |
| Python + pandas | `python3Packages.pandas` | `nix-shell -p python3Packages.pandas --run "python3 analyze.py"` |
| Python + requests | `python3Packages.requests` | `nix-shell -p python3Packages.requests --run "python3 fetch.py"` |
| xlsx2csv | `xlsx2csv` | `nix-shell -p xlsx2csv --run "xlsx2csv file.xlsx"` |
| csvkit | `csvkit` | `nix-shell -p csvkit --run "csvstat data.csv"` |
| `file` | `file` | `nix-shell -p file --run "file document.pdf"` |
| `jq` | `jq` | `nix-shell -p jq --run "jq '.key' data.json"` |
| `xmlstarlet` | `xmlstarlet` | `nix-shell -p xmlstarlet --run "xmlstarlet sel -t -v '//node' file.xml"` |
| `pandoc` | `pandoc` | `nix-shell -p pandoc --run "pandoc -f markdown -t html input.md"` |
| `pdftotext` | `poppler_utils` | `nix-shell -p poppler_utils --run "pdftotext document.pdf"` |
| `imagemagick` | `imagemagick` | `nix-shell -p imagemagick --run "convert input.jpg -resize 50% output.jpg"` |
| `ffmpeg` | `ffmpeg` | `nix-shell -p ffmpeg --run "ffmpeg -i input.mp4 output.mp3"` |
| `node` | `nodejs` | `nix-shell -p nodejs --run "node script.js"` |
| `gcc` | `gcc` | `nix-shell -p gcc --run "gcc -o program program.c"` |
| `make` | `gnumake` | `nix-shell -p gnumake --run "make"` |
| `unzip` | `unzip` | `nix-shell -p unzip --run "unzip archive.zip"` |
| `7z` | `p7zip` | `nix-shell -p p7zip --run "7z x archive.7z"` |

## Best practices

- **Combine all needed packages in one `nix-shell` call** rather than nesting multiple calls.
- **Use `--run` for automation** so the shell exits cleanly after the command.
- **Check `which <tool>` first** to see if it is already available before pulling in a package.
- **For Python packages, use the full attribute path**: `python3Packages.openpyxl`, not `openpyxl`.
- **Prefer `nix shell` or `nix run` when flakes are enabled**; use `nix-shell` when compatibility or legacy behavior is needed.
