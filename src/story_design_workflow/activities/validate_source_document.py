import dataclasses

from cadence import activity

from ..source_document_validation import validate_source_document


@activity.defn(name="validate_source_document")
async def validate_source_document_activity(analysis_path: str | None) -> dict:
    return dataclasses.asdict(validate_source_document(analysis_path))
