{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  buildInputs = with pkgs; [
    nodejs_24
    python3
    gcc
    gnumake
    pkg-config
    stdenv.cc.cc.lib
  ];

  # cadence-python-client's grpcio wheel links against libstdc++.so.6, which
  # isn't on the default Nix library path. See vault/services/cadence.md.
  shellHook = ''
    export LD_LIBRARY_PATH="${pkgs.stdenv.cc.cc.lib}/lib:$LD_LIBRARY_PATH"
    echo "Development environment loaded"
    echo "Node version: $(node --version)"
    echo "NPM version: $(npm --version)"
    echo "Python version: $(python3 --version)"
    echo "You can now run: npm install promptfoo"
  '';
}
