import dataclasses

from cadence import activity

from ..source_document_validation import validate_source_document


@activity.defn(name="validate_source_document")
async def validate_source_document_activity(story_document: str | None) -> dict:
    return dataclasses.asdict(validate_source_document(story_document))
