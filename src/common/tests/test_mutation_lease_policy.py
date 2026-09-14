from common.mutation_lease_policy import MutationLeasePolicyHandler
from common.mutation_lease_store import MutationLeaseStore


def test_lease_handler_releases_on_success() -> None:
    store = MutationLeaseStore()
    handler = MutationLeasePolicyHandler(store)

    with handler.lease(repo_key="repo", run_id="run-1", ttl=60) as token:
        assert token is not None

    assert store.is_held("repo") is False
