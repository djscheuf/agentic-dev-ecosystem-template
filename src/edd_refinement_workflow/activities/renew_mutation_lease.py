import time
from pathlib import Path

from cadence import activity

from common.mutation_lease_store import get_default_store


def renew_mutation_lease(repo_root: str, run_id: str, ttl: int) -> dict:
    """Extend the run's mutation lease so long-running iterations and approval
    waits keep the at-most-one-mutating-run invariant (AC-8)."""
    store = get_default_store(Path(repo_root) / ".process" / "mutation-leases.json")
    renewed = store.renew(repo_root, run_id, ttl)
    result = {"renewed": renewed}
    if renewed:
        dead_by = time.time() + ttl
        result["dead_by"] = dead_by
        from ..progress_record import ProgressRecordStore

        record_store = ProgressRecordStore(repo_root)
        record = record_store.create_or_resume(run_id, {})
        if record.get("mutation_lease"):
            record["mutation_lease"]["dead_by"] = dead_by
            record_store.save(run_id, record)
    return result


@activity.defn(name="renew_mutation_lease")
async def renew_mutation_lease_activity(
    repo_root: str, run_id: str, ttl: int
) -> dict:
    return renew_mutation_lease(repo_root, run_id, ttl)
