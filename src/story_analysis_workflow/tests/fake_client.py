"""Test double for the Cadence async client."""

from dataclasses import dataclass, field
from types import SimpleNamespace
from typing import Any, Optional


@dataclass
class ExecutionResult:
    workflow_id: str
    run_id: str = "test-run-id"


@dataclass
class FakeDomainStub:
    register_calls: list = field(default_factory=list)

    async def RegisterDomain(self, request):
        self.register_calls.append(request)
        return SimpleNamespace()


class FakeClient:
    """Records start, signal, and query calls and returns canned values."""

    def __init__(
        self,
        query_result: Optional[Any] = None,
        start_result: Optional[ExecutionResult] = None,
        query_error: Optional[Exception] = None,
        query_results: Optional[list] = None,
    ) -> None:
        self.query_result = query_result
        self.query_error = query_error
        # When set, consumed in order across successive query_workflow calls
        # (the last value repeats), e.g. to simulate a workflow that's still
        # `running` for a few polls before it finishes. Falls back to the
        # single `query_result` when not given.
        self.query_results = query_results
        self._query_call_count = 0
        self.start_result = start_result or ExecutionResult(workflow_id="test-wf")
        self.start_calls: list = []
        self.signal_calls: list = []
        self.query_calls: list = []
        self.domain_stub = FakeDomainStub()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def start_workflow(self, workflow: str, *args, **options):
        self.start_calls.append({"workflow": workflow, "args": args, "options": options})
        return self.start_result

    async def signal_workflow(self, workflow_id: str, run_id: str, signal_name: str, *signal_args):
        self.signal_calls.append(
            {
                "workflow_id": workflow_id,
                "run_id": run_id,
                "signal_name": signal_name,
                "signal_args": signal_args,
            }
        )

    async def query_workflow(self, workflow_id: str, run_id: str, query_type: str, *query_args, result_type=object, **kwargs):
        self.query_calls.append(
            {
                "workflow_id": workflow_id,
                "run_id": run_id,
                "query_type": query_type,
                "query_args": query_args,
                "result_type": result_type,
            }
        )
        if self.query_error:
            raise self.query_error
        if self.query_results is not None:
            index = min(self._query_call_count, len(self.query_results) - 1)
            self._query_call_count += 1
            return self.query_results[index]
        return self.query_result
