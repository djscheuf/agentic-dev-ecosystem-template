"""Client-side starter for the Story Analysis Cadence Workflow.

Starts a `StoryAnalysisWorkflow` execution from a story document path (or
verbatim text), deriving a deterministic `WorkflowID` when one isn't given so
re-running with the same input is rejected as a duplicate (per
`domain-task-list-retry-config.json`'s `workflow_id_reuse_policy`).
"""

import hashlib
import re
from typing import Optional

from .config import CadenceConfig, load_config

WORKFLOW_TYPE = "StoryAnalysisWorkflow"


def _default_workflow_id(story_document: str) -> str:
    """Derive a stable WorkflowID from the story document path/text.

    Combines a short, readable slug of the input with a hash of the full
    value so distinct story documents that happen to share a slug still get
    distinct IDs.
    """
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", story_document).strip("-").lower()
    slug = slug[-40:] or "story"
    digest = hashlib.sha256(story_document.encode("utf-8")).hexdigest()[:8]
    return f"story-analysis-{slug}-{digest}"


async def start_story_analysis_workflow(
    client,
    story_document: str,
    *,
    workflow_id: Optional[str] = None,
    config: Optional[CadenceConfig] = None,
    **engine_config,
):
    """Start a `StoryAnalysisWorkflow` execution.

    `engine_config` (e.g. `max_attempts`, `escalation_timeout_seconds`) is
    passed through as the workflow's `config` argument (see `workflow.py`).
    """
    config = config or load_config()
    resolved_workflow_id = workflow_id or _default_workflow_id(story_document)

    return await client.start_workflow(
        WORKFLOW_TYPE,
        story_document,
        engine_config,
        **config.to_start_workflow_kwargs(resolved_workflow_id),
    )
