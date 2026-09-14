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
    def inspect(self, repo_root: str) -> RepositoryStatus:
        result = subprocess.run(
            ["git", "-C", str(repo_root), "status", "--porcelain"],
            capture_output=True,
            text=True,
            check=True,
        )
        staged: list[str] = []
        modified: list[str] = []
        untracked: list[str] = []
        for line in result.stdout.splitlines():
            if not line:
                continue
            path = line[3:].strip()
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
