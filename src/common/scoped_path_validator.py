from pathlib import Path


class TargetScopeError(Exception):
    pass


class ScopedPathValidator:
    def validate(self, scoped_path: str, target_root: str) -> Path:
        target = Path(target_root).resolve()
        scoped = Path(scoped_path).resolve()
        scoped.relative_to(target)
        return scoped
