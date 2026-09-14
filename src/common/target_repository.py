import subprocess
from pathlib import Path


class TargetRepositoryResolutionError(Exception):
    pass


class TargetWorktreeResolver:
    def resolve(
        self, anchor_path: str | None = None, explicit_root: str | None = None
    ) -> Path:
        if anchor_path is None and explicit_root is None:
            raise TargetRepositoryResolutionError(
                "anchor_path or explicit_root is required"
            )
        anchor_root = self._git_root(Path(anchor_path).parent) if anchor_path else None
        if explicit_root is None:
            return anchor_root  # type: ignore[return-value]
        explicit_root = self._git_root(Path(explicit_root))
        if anchor_root is not None and anchor_root != explicit_root:
            raise TargetRepositoryResolutionError(
                f"Anchor-derived root {anchor_root} conflicts with explicit root {explicit_root}"
            )
        return explicit_root

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
