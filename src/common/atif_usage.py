import json
from collections.abc import Mapping
from pathlib import Path

from .harness import HarnessUsage


def read_atif_usage(path: Path) -> HarnessUsage | None:
    try:
        document = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return None
    metrics = document.get("final_metrics")
    if not isinstance(metrics, Mapping):
        return None
    return HarnessUsage(
        prompt_tokens=metrics.get("total_prompt_tokens"),
        completion_tokens=metrics.get("total_completion_tokens"),
        cached_tokens=metrics.get("total_cached_tokens"),
        cost_usd=float(metrics["total_cost_usd"]),
    )
