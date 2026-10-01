import posixpath
from pathlib import Path, PurePosixPath


class TargetScopeError(Exception):
    pass


class PathScopeChecker:
    def is_authorized(self, candidate: str, scope: list[str]) -> bool:
        candidate_parts = PurePosixPath(posixpath.normpath(candidate)).parts
        for entry in scope:
            if entry.endswith("/"):
                prefix_parts = PurePosixPath(entry).parts
                if (
                    len(candidate_parts) > len(prefix_parts)
                    and candidate_parts[: len(prefix_parts)] == prefix_parts
                ):
                    return True
            elif candidate_parts == PurePosixPath(entry).parts:
                return True
        return False


class ScopedPathValidator:
    def validate(self, scoped_path: str, target_root: str) -> Path:
        target = Path(target_root).resolve()
        scoped = Path(scoped_path).resolve()
        try:
            scoped.relative_to(target)
        except ValueError as exc:
            raise TargetScopeError(
                f"Scoped path {scoped} is outside target root {target}"
            ) from exc
        return scoped
