# Common nix-shell environments and examples

## Python data analysis

```bash
nix-shell -p python3Packages.pandas python3Packages.openpyxl --run "python3 analyze.py"
```

For Excel files, preserve sheets and formulas by using `openpyxl` or `pandas`, not a CSV conversion:

```bash
nix-shell -p python3Packages.openpyxl --run "python3 -c '
import openpyxl
wb = openpyxl.load_workbook(\"file.xlsx\")
for sheet in wb.sheetnames:
    print(f\"Sheet: {sheet}\")
    ws = wb[sheet]
    for row in ws.iter_rows(values_only=True):
        print(row)
'"
```

## Node.js

```bash
nix-shell -p nodejs --run "node script.js"
nix-shell -p nodejs yarn --run "yarn install && yarn build"
```

## Rust

```bash
nix-shell -p cargo rustc rustfmt --run "cargo build"
```

For a more complete Rust environment, consider a `flake.nix` with `rust-overlay` or `crane`.

## Haskell

```bash
nix-shell -p ghc --run "ghc script.hs"
nix-shell -p haskellPackages.ghcWithPackages (ps: [ ps.cabal-install ps.stack ]) --run "cabal build"
```

Note: for complex Haskell expressions, a `shell.nix` or flake is usually easier than a one-liner.

## C/C++ build

```bash
nix-shell -p gcc gnumake cmake --run "make"
```

## General project shell.nix

```nix
{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  buildInputs = with pkgs; [
    git
    jq
    nodejs
    python3
    python3Packages.requests
  ];
}
```

## Real-world example: read Excel without losing data

**Bad approach:**

```bash
python3 script.py        # fails: python3 not installed
libreoffice --convert-to csv file.xlsx   # loses multiple sheets and formulas
```

**Good approach:**

```bash
# Option 1: read all sheets with openpyxl
nix-shell -p python3Packages.openpyxl --run "python3 -c '
import openpyxl
wb = openpyxl.load_workbook(\"file.xlsx\")
for sheet in wb.sheetnames:
    print(f\"Sheet: {sheet}\")
    for row in wb[sheet].iter_rows(values_only=True):
        print(row)
'"

# Option 2: load all sheets into pandas
nix-shell -p python3Packages.pandas python3Packages.openpyxl --run "python3 -c '
import pandas as pd
dfs = pd.read_excel(\"file.xlsx\", sheet_name=None)
for name, df in dfs.items():
    print(f\"Sheet: {name}\")
    print(df.head())
'"

# Option 3: only if CSV is truly sufficient
nix-shell -p xlsx2csv --run "xlsx2csv --all file.xlsx output_dir/"
```

## Real-world example: parse JSON

```bash
nix-shell -p jq --run "jq '.key' data.json"
```

## Real-world example: extract PDF text

```bash
nix-shell -p poppler_utils --run "pdftotext document.pdf -"
```

## Real-world example: convert an image

```bash
nix-shell -p imagemagick --run "convert input.jpg -resize 50% output.jpg"
```

## Real-world example: process a video

```bash
nix-shell -p ffmpeg --run "ffmpeg -i input.mp4 -vn -acodec libmp3lame output.mp3"
```

## Real-world example: archive extraction

```bash
nix-shell -p unzip --run "unzip archive.zip"
nix-shell -p p7zip --run "7z x archive.7z"
```

## Best practices

- **Preserve data integrity**: use specialized tools rather than lossy conversions.
- **Combine tools in one shell**: avoid multiple sequential `nix-shell` calls.
- **Use `shell.nix` or a flake for projects** you return to frequently.
- **For Python, use `python3Packages.<name>`** for libraries.
- **Don't install one-off tools globally** with `nix-env` or `nix profile`.
