import json
from collections.abc import Mapping
from pathlib import Path

from .harness import HarnessUsage
from .harness_usage import coerce_cost, coerce_token


def read_atif_usage_result(path: Path) -> tuple[HarnessUsage | None, str | None]:
    try:
        content = path.read_text()
    except FileNotFoundError:
        return None, "missing_export"
    except OSError:
        return None, "unreadable_export"
    try:
        document = json.loads(content)
    except json.JSONDecodeError:
        return None, "malformed_json"
    if not isinstance(document, Mapping):
        return None, "invalid_document"
    metrics = document.get("final_metrics")
    if not isinstance(metrics, Mapping):
        return None, "invalid_final_metrics"
    return HarnessUsage(
        prompt_tokens=coerce_token(metrics.get("total_prompt_tokens")),
        completion_tokens=coerce_token(metrics.get("total_completion_tokens")),
        cached_tokens=coerce_token(metrics.get("total_cached_tokens")),
        cost_usd=coerce_cost(metrics.get("total_cost_usd")),
    ), None


def read_atif_usage(path: Path) -> HarnessUsage | None:
    return read_atif_usage_result(path)[0]
