import json

from common.atif_usage import read_atif_usage
from common.harness import HarnessUsage


def test_read_atif_usage_normalizes_supported_metrics(tmp_path) -> None:
    export_path = tmp_path / "trajectory.json"
    export_path.write_text(
        json.dumps(
            {
                "final_metrics": {
                    "total_prompt_tokens": 100,
                    "total_completion_tokens": 20,
                    "total_cached_tokens": 40,
                    "total_cost_usd": 2,
                    "total_credits": 7,
                }
            }
        )
    )

    usage = read_atif_usage(export_path)

    assert usage == HarnessUsage(
        prompt_tokens=100,
        completion_tokens=20,
        cached_tokens=40,
        cost_usd=2.0,
    )


def test_read_atif_usage_returns_none_for_missing_or_invalid_document(tmp_path) -> None:
    invalid_path = tmp_path / "invalid.json"
    invalid_path.write_text("not json")

    results = [
        read_atif_usage(tmp_path / "missing.json"),
        read_atif_usage(tmp_path),
        read_atif_usage(invalid_path),
    ]

    assert results == [None, None, None]
