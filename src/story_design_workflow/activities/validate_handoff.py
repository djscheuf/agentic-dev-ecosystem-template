import dataclasses

from cadence import activity

from ..handoff_validation import HandoffValidationRequest, validate_handoff


@activity.defn(name="validate_handoff")
async def validate_handoff_activity(
    output_path: str,
    schema_path: str,
    previous_activity_name: str = "",
    workflow_id: str = "",
    run_id: str = "",
    attempt: int = 0,
) -> dict:
    request = HandoffValidationRequest(
        output_path=output_path,
        previous_activity_name=previous_activity_name,
        workflow_id=workflow_id,
        run_id=run_id,
        attempt=attempt,
        schema_path=schema_path,
    )
    return dataclasses.asdict(validate_handoff(request))
