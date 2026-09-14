import dataclasses
import subprocess
from pathlib import Path


@dataclasses.dataclass
class RepositoryStatus:
    is_clean: bool
    staged: list[str]
    modified: list[str]
    untracked: list[str]


class RepositoryStatusInspector:
    def inspect(
        self, repo_root: str, scratch_globs: list[str] | None = None
    ) -> RepositoryStatus:
        result = subprocess.run(
            ["git", "-C", str(repo_root), "status", "--porcelain", "-uall"],
            capture_output=True,
            text=True,
            check=True,
        )
        scratch_globs = scratch_globs or []
        staged: list[str] = []
        modified: list[str] = []
        untracked: list[str] = []
        for line in result.stdout.splitlines():
            if not line:
                continue
            path = line[3:].strip()
            if any(Path(path).match(glob) for glob in scratch_globs):
                continue
            if line.startswith("??"):
                untracked.append(path)
            elif line[1] == "M":
                modified.append(path)
            elif line[0] in "MADRC":
                staged.append(path)
        return RepositoryStatus(
            is_clean=not (staged or modified or untracked),
            staged=staged,
            modified=modified,
            untracked=untracked,
        )
