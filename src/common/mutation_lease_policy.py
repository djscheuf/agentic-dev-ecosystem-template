from types import TracebackType
from typing import Optional

from common.mutation_lease_store import MutationLeaseStore


class LeaseConflictError(Exception):
    pass


class _LeaseHandle:
    def __init__(
        self, store: MutationLeaseStore, repo_key: str, run_id: str, token: str
    ) -> None:
        self._store = store
        self._repo_key = repo_key
        self._run_id = run_id
        self._token = token

    def __enter__(self) -> str:
        return self._token

    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc: Optional[BaseException],
        tb: Optional[TracebackType],
    ) -> None:
        self._store.release(self._repo_key, self._run_id)


class MutationLeasePolicyHandler:
    def __init__(self, store: MutationLeaseStore) -> None:
        self._store = store

    def lease(self, repo_key: str, run_id: str, ttl: int) -> _LeaseHandle:
        token = self._store.acquire(repo_key, run_id, ttl)
        if token is None:
            raise LeaseConflictError(
                f"Repository {repo_key} is already held by another run"
            )
        return _LeaseHandle(self._store, repo_key, run_id, token)
