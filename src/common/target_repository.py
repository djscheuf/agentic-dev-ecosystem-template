import subprocess
from pathlib import Path


class TargetRepositoryResolutionError(Exception):
    pass


class TargetWorktreeResolver:
    def resolve(self, anchor_path: str, explicit_root: str | None = None) -> Path:
        anchor = Path(anchor_path)
        anchor_root = self._git_root(anchor.parent)
        if explicit_root is None:
            return anchor_root
        explicit_root = self._git_root(Path(explicit_root))
        if anchor_root != explicit_root:
            raise TargetRepositoryResolutionError(
                f"Anchor-derived root {anchor_root} conflicts with explicit root {explicit_root}"
            )
        return anchor_root

    def _git_root(self, cwd: Path) -> Path:
        try:
            result = subprocess.run(
                ["git", "-C", str(cwd), "rev-parse", "--show-toplevel"],
                capture_output=True,
                text=True,
                check=True,
            )
        except subprocess.CalledProcessError as exc:
            raise TargetRepositoryResolutionError(
                f"Could not resolve Git worktree for {cwd}: {exc.stderr}"
            ) from exc
        return Path(result.stdout.strip()).resolve()
