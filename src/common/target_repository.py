import subprocess
from pathlib import Path


class TargetRepositoryResolutionError(Exception):
    pass


class TargetWorktreeResolver:
    def resolve(self, anchor_path: str) -> Path:
        anchor = Path(anchor_path)
        try:
            result = subprocess.run(
                ["git", "-C", str(anchor.parent), "rev-parse", "--show-toplevel"],
                capture_output=True,
                text=True,
                check=True,
            )
        except subprocess.CalledProcessError as exc:
            raise TargetRepositoryResolutionError(
                f"Could not resolve Git worktree for {anchor}: {exc.stderr}"
            ) from exc
        return Path(result.stdout.strip()).resolve()
