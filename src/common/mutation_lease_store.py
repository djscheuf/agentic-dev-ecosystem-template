import uuid


class MutationLeaseStore:
    def __init__(self):
        self._leases: dict[str, str] = {}

    def acquire(self, repo_key: str, run_id: str, ttl: int) -> str:
        token = str(uuid.uuid4())
        self._leases[repo_key] = token
        return token

    def is_held(self, repo_key: str) -> bool:
        return repo_key in self._leases
