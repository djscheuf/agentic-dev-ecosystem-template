"""CLI entry point for manually invoking a single Story Analysis Activity
against a real Cadence server.

Backs `scripts/run-single-activity`. Starts a `SingleActivityWorkflow`
(`orchestrator.single_activity_workflow`) that schedules exactly the named
Activity on the already-running `orchestrator.worker`, then polls its
`get_result` Query until it finishes. Requires
`scripts/start-workflow-engine.sh` to already be running (a local Cadence
server + `orchestrator.worker` polling the configured task list) -- this is
a Cadence *client*, it does not call the Activity directly, so retries,
timeouts, and task-list routing all behave exactly as they do for a normal
`StoryAnalysisWorkflow` run.

`repair_story_analysis` is intentionally not supported here: it needs two
input files (the analysis and its grade), not the single input file this
script accepts.
"""

import asyncio
import json
import sys
import uuid
from pathlib import Path
from typing import Any, Callable, Optional, Sequence

from cadence.client import Client

from .config import CadenceConfig, load_config
from .workflow_logger import client_log_context, get_client_logger
from .queries import get_activity_result

REPO_ROOT = Path(__file__).resolve().parents[2]
ClientFactory = Callable[[CadenceConfig], Client]
WORKFLOW_TYPE = "SingleActivityWorkflow"
KNOWN_ACTIVITY_NAMES = frozenset(
    {"extract_story_intent", "analyze_story", "grade_story_analysis", "repair_story_analysis"}
)
UNSUPPORTED_ACTIVITY_NAMES = {
    "repair_story_analysis": "needs two input files (analysis + grade)",
}
SUPPORTED_ACTIVITY_NAMES = KNOWN_ACTIVITY_NAMES - set(UNSUPPORTED_ACTIVITY_NAMES)

DEFAULT_POLL_INTERVAL_SECONDS = 2.0
DEFAULT_WAIT_TIMEOUT_SECONDS = 300.0

_USAGE_TEMPLATE = """\
Usage: run-single-activity <activity_name> <input_file>
       run-single-activity --help

Manually invoke a single Story Analysis Activity against a real Cadence
server, by starting a SingleActivityWorkflow that schedules exactly that
Activity on the already-running orchestrator worker.

Requires the local Cadence stack + worker to already be running:
  scripts/start-workflow-engine.sh

Arguments:
  activity_name   One of: {names}
  input_file      Path to the activity's input document (repo-relative or absolute).

Examples:
  run-single-activity extract_story_intent docs/reqs/workflow-orchestration/story.md
  run-single-activity analyze_story docs/reqs/workflow-orchestration/story.intent.json
  run-single-activity grade_story_analysis docs/reqs/workflow-orchestration/story.analysis.json

Unsupported activities:
{unsupported}
"""


def _usage_text() -> str:
    return _USAGE_TEMPLATE.format(
        names=", ".join(sorted(SUPPORTED_ACTIVITY_NAMES)),
        unsupported="\n".join(
            f"  {name} - {reason}" for name, reason in sorted(UNSUPPORTED_ACTIVITY_NAMES.items())
        ),
    )


def _resolve_input_file(raw_path: str, *, repo_root: Path) -> Path:
    path = Path(raw_path)
    return path if path.is_absolute() else repo_root / path


def _relative_to_repo_root(path: Path, *, repo_root: Path) -> str:
    try:
        return str(path.relative_to(repo_root))
    except ValueError:
        return str(path)


def _build_activity_args(activity_name: str, relative_input: str) -> list:
    """Adapt this script's single "input file" argument to the Activity's
    actual signature (see `docs/reqs/workflow-orchestration/activity-contracts.md`)."""
    if activity_name == "extract_story_intent":
        return [[relative_input]]
    return [relative_input]


def _default_client_factory(config: CadenceConfig) -> Client:
    return Client(domain=config.domain, target=config.cadence_target)


def _failure_hint() -> str:
    return (
        "Check the Cadence Web UI (http://localhost:8088) and scripts/.run/worker.log\n"
        "for the activity task's history and the worker's own error output."
    )


async def _poll_for_result(
    client,
    workflow_id: str,
    run_id: str,
    *,
    poll_interval_seconds: float,
    wait_timeout_seconds: float,
    sleep: Callable[[float], Any] = asyncio.sleep,
) -> dict:
    loop = asyncio.get_event_loop()
    deadline = loop.time() + wait_timeout_seconds
    while True:
        status = await get_activity_result(client, workflow_id, run_id=run_id)
        if status.get("status") != "running":
            return status
        if loop.time() > deadline:
            return {
                "status": "timed_out",
                "error": f"Timed out after {wait_timeout_seconds}s waiting for workflow {workflow_id!r} to finish",
            }
        await sleep(poll_interval_seconds)


async def run_single_activity_main(
    argv: Sequence[str],
    *,
    repo_root: Path = REPO_ROOT,
    config: Optional[CadenceConfig] = None,
    client_factory: Optional[ClientFactory] = None,
    poll_interval_seconds: float = DEFAULT_POLL_INTERVAL_SECONDS,
    wait_timeout_seconds: float = DEFAULT_WAIT_TIMEOUT_SECONDS,
) -> int:
    if not argv or argv[0] in ("-h", "--help"):
        print(_usage_text())
        return 0

    if len(argv) != 2:
        print(f"Error: expected exactly 2 arguments, got {len(argv)}.\n", file=sys.stderr)
        print(_usage_text(), file=sys.stderr)
        return 1

    activity_name, input_file_arg = argv

    if activity_name in UNSUPPORTED_ACTIVITY_NAMES:
        print(
            f"Error: activity '{activity_name}' is not supported by this script "
            f"({UNSUPPORTED_ACTIVITY_NAMES[activity_name]}).\n"
            f"Supported activities: {', '.join(sorted(SUPPORTED_ACTIVITY_NAMES))}",
            file=sys.stderr,
        )
        return 1
    if activity_name not in SUPPORTED_ACTIVITY_NAMES:
        print(
            f"Error: unrecognized activity '{activity_name}'.\n"
            f"Supported activities: {', '.join(sorted(SUPPORTED_ACTIVITY_NAMES))}",
            file=sys.stderr,
        )
        return 1

    input_path = _resolve_input_file(input_file_arg, repo_root=repo_root)
    if not input_path.is_file():
        print(f"Error: input file not found: {input_path}", file=sys.stderr)
        return 1

    relative_input = _relative_to_repo_root(input_path, repo_root=repo_root)
    resolved_config = config or load_config()
    factory = client_factory or _default_client_factory
    workflow_id = f"single-activity-{activity_name}-{uuid.uuid4().hex[:8]}"

    print(f"Starting '{WORKFLOW_TYPE}' for activity '{activity_name}' with input '{relative_input}'...")
    client = factory(resolved_config)
    async with client:
        execution = await client.start_workflow(
            WORKFLOW_TYPE,
            activity_name,
            _build_activity_args(activity_name, relative_input),
            **resolved_config.to_start_workflow_kwargs(workflow_id),
        )
        print(f"Started workflow_id={execution.workflow_id!r} run_id={execution.run_id!r}. Waiting for result...")

        with client_log_context(execution.workflow_id, execution.run_id):
            logger = get_client_logger()
            logger.info(
                "Started SingleActivityWorkflow for activity=%s input=%s",
                activity_name,
                relative_input,
            )
            status = await _poll_for_result(
                client,
                execution.workflow_id,
                execution.run_id,
                poll_interval_seconds=poll_interval_seconds,
                wait_timeout_seconds=wait_timeout_seconds,
            )

            if status.get("status") == "succeeded":
                logger.info("Activity succeeded: %s", status)
                print(f"\nActivity '{activity_name}' succeeded:")
                print(json.dumps(status["result"], indent=2))
                return 0

            logger.error("Activity failed: %s", status)
            print(
                f"\nActivity '{activity_name}' {status.get('status', 'failed')}: {status.get('error')}",
                file=sys.stderr,
            )
            print(f"\n{_failure_hint()}", file=sys.stderr)
            return 1


def main(argv: Optional[Sequence[str]] = None) -> None:
    sys.exit(asyncio.run(run_single_activity_main(sys.argv[1:] if argv is None else argv)))


if __name__ == "__main__":
    main()
