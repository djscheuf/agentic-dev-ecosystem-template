import json
from pathlib import Path

from .harness import HarnessUsage


def read_atif_usage(path: Path) -> HarnessUsage | None:
    document = json.loads(path.read_text())
    metrics = document["final_metrics"]
    return HarnessUsage(
        prompt_tokens=metrics.get("total_prompt_tokens"),
        completion_tokens=metrics.get("total_completion_tokens"),
        cached_tokens=metrics.get("total_cached_tokens"),
        cost_usd=float(metrics["total_cost_usd"]),
    )
