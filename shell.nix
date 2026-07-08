{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  buildInputs = with pkgs; [
    nodejs_24
    python3
    gcc
    gnumake
    pkg-config
  ];

  shellHook = ''
    echo "Development environment loaded"
    echo "Node version: $(node --version)"
    echo "NPM version: $(npm --version)"
    echo "You can now run: npm install promptfoo"
  '';
}
