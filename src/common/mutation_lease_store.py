import fcntl
import json
import time
import uuid
from pathlib import Path
from typing import Any


_DEFAULT_STORE: "MutationLeaseStore | None" = None


def get_default_store(store_path: Path | str | None = None) -> "MutationLeaseStore":
    global _DEFAULT_STORE
    if store_path is not None:
        return MutationLeaseStore(store_path)
    if _DEFAULT_STORE is None:
        _DEFAULT_STORE = MutationLeaseStore()
    return _DEFAULT_STORE


class MutationLeaseStore:
    def __init__(self, store_path: Path | str | None = None) -> None:
        self._store_path = Path(store_path) if store_path is not None else None
        self._leases: dict[str, tuple[str, str, float]] = (
            {} if self._store_path is None else None
        )
        if self._store_path is not None:
            self._store_path.parent.mkdir(parents=True, exist_ok=True)

    def acquire(self, repo_key: str, run_id: str, ttl: int) -> str | None:
        def _mutate(leases: dict[str, tuple[str, str, float]]) -> str | None:
            self._expire(leases)
            if repo_key in leases:
                held_run_id, _, _ = leases[repo_key]
                if held_run_id != run_id:
                    return None
            token = str(uuid.uuid4())
            leases[repo_key] = (run_id, token, time.monotonic() + ttl)
            return token

        return self._atomic(_mutate)

    def release(self, repo_key: str, run_id: str) -> bool:
        def _mutate(leases: dict[str, tuple[str, str, float]]) -> bool:
            self._expire(leases)
            if repo_key not in leases:
                return False
            held_run_id, _, _ = leases[repo_key]
            if held_run_id != run_id:
                return False
            del leases[repo_key]
            return True

        return self._atomic(_mutate)

    def is_held(self, repo_key: str) -> bool:
        def _read(leases: dict[str, tuple[str, str, float]]) -> bool:
            self._expire(leases)
            return repo_key in leases

        return self._atomic(_read)

    def _expire(
        self, leases: dict[str, tuple[str, str, float]]
    ) -> dict[str, tuple[str, str, float]]:
        now = time.monotonic()
        for key in list(leases.keys()):
            if leases[key][2] <= now:
                del leases[key]
        return leases

    def _atomic(self, fn: Any) -> Any:
        if self._store_path is None:
            leases = self._load()
            result = fn(leases)
            self._save(leases)
            return result

        lock_path = self._store_path.with_suffix(".lock")
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        with open(lock_path, "w") as lock_file:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
            try:
                leases = self._load()
                result = fn(leases)
                self._save(leases)
                return result
            finally:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)

    def _load(self) -> dict[str, tuple[str, str, float]]:
        if self._store_path is None:
            return self._leases
        if not self._store_path.exists():
            return {}
        try:
            raw = json.loads(self._store_path.read_text())
        except (json.JSONDecodeError, FileNotFoundError):
            return {}
        leases: dict[str, tuple[str, str, float]] = {}
        for key, value in raw.items():
            if isinstance(value, list) and len(value) == 3:
                leases[key] = (value[0], value[1], float(value[2]))
        return leases

    def _save(self, leases: dict[str, tuple[str, str, float]]) -> None:
        if self._store_path is None:
            self._leases = leases
            return
        serializable = {k: [v[0], v[1], v[2]] for k, v in leases.items()}
        self._store_path.write_text(json.dumps(serializable, indent=2))
