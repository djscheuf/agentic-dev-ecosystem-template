from collections.abc import Callable
from types import TracebackType
from typing import Any, Optional

from common.mutation_lease_store import MutationLeaseStore


class LeaseConflictError(Exception):
    pass


class _LeaseHandle:
    def __init__(
        self,
        store: MutationLeaseStore,
        repo_key: str,
        run_id: str,
        token: str,
        on_event: Optional[Callable[..., None]],
    ) -> None:
        self._store = store
        self._repo_key = repo_key
        self._run_id = run_id
        self._token = token
        self._on_event = on_event

    def _emit(self, name: str, **data: Any) -> None:
        if self._on_event is not None:
            self._on_event(name, **data)

    def __enter__(self) -> str:
        self._emit(
            "AcquireMutationLease",
            repo_key=self._repo_key,
            run_id=self._run_id,
            token=self._token,
        )
        return self._token

    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc: Optional[BaseException],
        tb: Optional[TracebackType],
    ) -> None:
        self._store.release(self._repo_key, self._run_id)
        self._emit(
            "ReleaseMutationLease",
            repo_key=self._repo_key,
            run_id=self._run_id,
        )


class MutationLeasePolicyHandler:
    def __init__(
        self,
        store: MutationLeaseStore,
        on_event: Optional[Callable[..., None]] = None,
    ) -> None:
        self._store = store
        self._on_event = on_event

    def _emit(self, name: str, **data: Any) -> None:
        if self._on_event is not None:
            self._on_event(name, **data)

    def lease(self, repo_key: str, run_id: str, ttl: int) -> _LeaseHandle:
        token = self._store.acquire(repo_key, run_id, ttl)
        if token is None:
            self._emit(
                "AcquireMutationLease",
                repo_key=repo_key,
                run_id=run_id,
                error="conflict",
            )
            raise LeaseConflictError(
                f"Repository {repo_key} is already held by another run"
            )
        return _LeaseHandle(self._store, repo_key, run_id, token, self._on_event)
