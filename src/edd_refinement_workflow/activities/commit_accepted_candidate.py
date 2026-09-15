import subprocess
from collections.abc import Callable
from datetime import UTC, datetime

from cadence import activity


class CommitAcceptedCandidateActivity:
    def __init__(
        self,
        store,
        commit: Callable[[str], str],
        now: Callable[[], str] | None = None,
    ) -> None:
        self.store = store
        self.commit = commit
        self.now = now or (lambda: datetime.now(UTC).isoformat())

    def run(self, run_id: str, metric: dict) -> dict:
        record = self.store.create_or_resume(run_id, {})
        candidate_id = metric["candidate_id"]
        commit_hash = self.commit(f"Accept EDD candidate {candidate_id}")
        best_state = {
            "candidate_id": candidate_id,
            "commit": commit_hash,
            "metrics": metric,
            "accepted_at": self.now(),
        }
        record["best_accepted_state"] = best_state
        record["consecutive_confirmed_regressions"] = 0
        record["candidate_history"] = record.get("candidate_history", []) + [
            {
                "candidate_id": candidate_id,
                "status": "accepted",
                "commit": commit_hash,
            }
        ]
        self.store.save(run_id, record)
        return best_state


def _commit_repository(repo_root: str, message: str) -> str:
    subprocess.run(["git", "-C", repo_root, "add", "-A"], check=True)
    subprocess.run(["git", "-C", repo_root, "commit", "-m", message], check=True)
    completed = subprocess.run(
        ["git", "-C", repo_root, "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    )
    return completed.stdout.strip()


@activity.defn(name="commit_accepted_candidate")
async def commit_accepted_candidate_activity(run_id: str, metric: dict, repo_root: str) -> dict:
    from ..progress_record import ProgressRecordStore

    return CommitAcceptedCandidateActivity(
        ProgressRecordStore(repo_root),
        commit=lambda message: _commit_repository(repo_root, message),
    ).run(run_id, metric)
