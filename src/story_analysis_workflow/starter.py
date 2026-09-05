"""Client-side starter for the Story Analysis Cadence Workflow.

Starts a `StoryAnalysisWorkflow` execution from a story document path (or
verbatim text), deriving a `WorkflowID` when one isn't given from the input's
name plus a "zettel id" -- a `YYYYMMDDHHmm` timestamp (24-hour, local to the
caller) taken at kickoff time. E.g. `example_story.md` started at 14:30 on
2026-08-31 becomes `story-analysis-example_story_202608311430`. Unlike the
previous content-hash-based id, two kickoffs of the exact same story now get
distinct WorkflowIDs (down to the minute) instead of being deduplicated; see
`vault/decisions/` for the rationale.
"""

import re
from datetime import datetime
from typing import Optional

from .workflow_logger import client_log_context, get_client_logger

from .config import CadenceConfig, load_config

WORKFLOW_TYPE = "StoryAnalysisWorkflow"

_PATH_LIKE_RE = re.compile(r"[\\/]|\.[A-Za-z0-9]{1,8}$")
_EXTENSION_RE = re.compile(r"\.[A-Za-z0-9]{1,8}$")
_UNSAFE_CHARS_RE = re.compile(r"[^a-zA-Z0-9_-]+")


def _slugify(text: str, max_len: int = 40) -> str:
    slug = _UNSAFE_CHARS_RE.sub("_", text).strip("_").lower()
    return slug[-max_len:] or "story"


def _name_component(story_document: str) -> str:
    """Derive the readable "name" portion of the WorkflowID.

    File-path-looking inputs (containing a path separator, or ending in a
    short file extension like `.md`) use their basename with the extension
    stripped, e.g. `docs/example_story.md` -> `example_story`. Verbatim story
    text falls back to a slug of the whole string, as before.
    """
    stripped = story_document.strip()
    if _PATH_LIKE_RE.search(stripped):
        base = re.split(r"[\\/]", stripped)[-1]
        base = _EXTENSION_RE.sub("", base)
    else:
        base = stripped
    return _slugify(base)


def _zettel_id(when: Optional[datetime] = None) -> str:
    """24-hour, local-time `YYYYMMDDHHmm` timestamp for the kickoff moment."""
    return (when or datetime.now()).strftime("%Y%m%d%H%M")


def _default_workflow_id(story_document: str, *, when: Optional[datetime] = None) -> str:
    """Derive a `WorkflowID` from the story document's name and kickoff time."""
    return f"story-analysis-{_name_component(story_document)}_{_zettel_id(when)}"


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

    execution = await client.start_workflow(
        WORKFLOW_TYPE,
        story_document,
        engine_config,
        **config.to_start_workflow_kwargs(resolved_workflow_id),
    )
    with client_log_context(execution.workflow_id, execution.run_id):
        logger = get_client_logger()
        logger.info(
            "Started StoryAnalysisWorkflow workflow_id=%s run_id=%s story=%s",
            execution.workflow_id,
            execution.run_id,
            story_document,
        )
    return execution
