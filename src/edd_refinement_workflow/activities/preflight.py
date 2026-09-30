import dataclasses
import json
from pathlib import Path

from cadence import activity

from common.preflight import resolve_and_validate_target_repository

from ..input import EddRefinementInput

# Run-lifetime lease TTL (CR-02): deliberately decoupled from
# eval_timeout_seconds. The workflow renews the lease each iteration and
# before approval waits, so this only needs to cover the longest single
# stretch without renewal (a human approval wait or one evaluation).
DEFAULT_LEASE_TTL_SECONDS = 3600


def run_preflight(input_path: str, workflow_run_id: str) -> dict:
    """Resolve and validate the target repository inside the workflow, then
    build the normalized request the rest of the workflow consumes."""
    input_path = Path(input_path)
    raw_input = json.loads(input_path.read_text(encoding="utf-8"))
    input_document = EddRefinementInput.from_path(input_path)

    preflight = resolve_and_validate_target_repository(
        anchor_path=str(input_document.skill_folder),
        explicit_root=None,
        scoped_paths=[str(p) for p in input_document.modification_scope],
        skill_name=input_document.skill_folder.name,
        evaluation_path=str(input_document.eval_config),
        additional_paths=[
            str(input_document.test_cases),
            *(str(p) for p in input_document.related_content),
        ],
        run_id=workflow_run_id,
        lease_ttl=DEFAULT_LEASE_TTL_SECONDS,
    )

    result = {
        "preflight_result": dataclasses.asdict(preflight),
        "request": None,
    }
    if preflight.status != "success":
        return result

    profile = {
        "command": input_document.test_command,
        "configuration": str(input_document.eval_config),
        "provider": preflight.provider or "default",
        "timeout": input_document.limits["eval_timeout_seconds"],
        "limits": input_document.limits,
        "measurement_context": "baseline",
        "test_cases": str(input_document.test_cases),
        "coverage_metadata_property": input_document.coverage_metadata_property,
        "inspect_command": input_document.inspect_command,
    }

    result["request"] = {
        "workflow_run_id": workflow_run_id,
        "profile": profile,
        "input_path": str(input_path),
        "input_parent": str(input_document.input_parent),
        "edd_input": raw_input,
        "approval_timeout_seconds": 3600,
        "regression_stop_threshold": 3,
        "next_step_token_estimate": 0,
        "test_cases_path": str(input_document.test_cases),
        "coverage_metadata_property": input_document.coverage_metadata_property,
        "lease_ttl": DEFAULT_LEASE_TTL_SECONDS,
    }
    return result


@activity.defn(name="preflight")
async def preflight_activity(input_path: str, workflow_run_id: str) -> dict:
    return run_preflight(input_path, workflow_run_id)
