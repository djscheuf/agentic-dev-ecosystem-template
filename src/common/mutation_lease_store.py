import uuid


class MutationLeaseStore:
    def __init__(self):
        self._leases: dict[str, tuple[str, str]] = {}

    def acquire(self, repo_key: str, run_id: str, ttl: int) -> str | None:
        if repo_key in self._leases:
            held_run_id, _ = self._leases[repo_key]
            if held_run_id != run_id:
                return None
        token = str(uuid.uuid4())
        self._leases[repo_key] = (run_id, token)
        return token

    def release(self, repo_key: str, run_id: str) -> bool:
        if repo_key not in self._leases:
            return False
        held_run_id, _ = self._leases[repo_key]
        if held_run_id != run_id:
            return False
        del self._leases[repo_key]
        return True

    def is_held(self, repo_key: str) -> bool:
        return repo_key in self._leases
