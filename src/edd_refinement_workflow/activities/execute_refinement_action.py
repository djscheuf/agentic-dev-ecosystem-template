from collections.abc import Callable


class ExecuteRefinementActionActivity:
    def __init__(self, harness_runner: Callable[..., object]) -> None:
        self.harness_runner = harness_runner

    def run(
        self,
        run_id: str,
        planning: dict,
        approved_diff_hash: str | None,
        repo_root: str,
    ):
        if planning.get("requires_approval") and approved_diff_hash is None:
            raise ValueError("missing_approval")
        return self.harness_runner(
            run_id=run_id,
            planning=planning,
            repo_root=repo_root,
        )
