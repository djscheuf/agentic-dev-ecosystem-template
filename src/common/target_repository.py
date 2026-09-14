import subprocess
from pathlib import Path


class TargetWorktreeResolver:
    def resolve(self, anchor_path: str) -> Path:
        anchor = Path(anchor_path)
        result = subprocess.run(
            ["git", "-C", str(anchor.parent), "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True,
        )
        return Path(result.stdout.strip()).resolve()
