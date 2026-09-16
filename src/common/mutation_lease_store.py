import time
import uuid


_DEFAULT_STORE: "MutationLeaseStore | None" = None


def get_default_store() -> "MutationLeaseStore":
    global _DEFAULT_STORE
    if _DEFAULT_STORE is None:
        _DEFAULT_STORE = MutationLeaseStore()
    return _DEFAULT_STORE


class MutationLeaseStore:
    def __init__(self):
        self._leases: dict[str, tuple[str, str, float]] = {}

    def acquire(self, repo_key: str, run_id: str, ttl: int) -> str | None:
        self._expire_if_needed(repo_key)
        if repo_key in self._leases:
            held_run_id, _, _ = self._leases[repo_key]
            if held_run_id != run_id:
                return None
        token = str(uuid.uuid4())
        self._leases[repo_key] = (run_id, token, time.monotonic() + ttl)
        return token

    def release(self, repo_key: str, run_id: str) -> bool:
        self._expire_if_needed(repo_key)
        if repo_key not in self._leases:
            return False
        held_run_id, _, _ = self._leases[repo_key]
        if held_run_id != run_id:
            return False
        del self._leases[repo_key]
        return True

    def is_held(self, repo_key: str) -> bool:
        self._expire_if_needed(repo_key)
        return repo_key in self._leases

    def _expire_if_needed(self, repo_key: str) -> None:
        if repo_key not in self._leases:
            return
        _, _, expires_at = self._leases[repo_key]
        if time.monotonic() >= expires_at:
            del self._leases[repo_key]
