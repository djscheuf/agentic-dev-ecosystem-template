"""`edd-refinement-cli` -- start/query/approve/reject the EDD Refinement Workflow."""

import argparse
import asyncio
import dataclasses
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional, Sequence

from cadence.client import Client
from cadence.error import EntityNotExistsError

from .config import CadenceConfig, load_config
from .input import EddRefinementInput, EddRefinementInputError

ClientFactory = Callable[[CadenceConfig], Client]


def _default_client_factory(config: CadenceConfig) -> Client:
    return Client(domain=config.domain, target=config.cadence_target)


def _slugify(text: str, max_len: int = 40) -> str:
    slug = re.sub(r"[^a-zA-Z0-9_-]+", "_", text).strip("_").lower()
    return slug[-max_len:] or "edd"


def _default_workflow_id(input_path: str | Path, *, when: Optional[datetime] = None) -> str:
    stem = Path(input_path).stem
    return f"edd-refinement-{_slugify(stem)}_{(when or datetime.now()).strftime('%Y%m%d%H%M')}"


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="edd-refinement-cli")
    parser.add_argument("--domain")
    parser.add_argument("--task-list")
    parser.add_argument("--target")
    subparsers = parser.add_subparsers(dest="command", required=True)

    start = subparsers.add_parser("start", help="Start an EDD Refinement Workflow execution")
    start.add_argument("input_path")
    start.add_argument("--workflow-id")

    query = subparsers.add_parser("query", help="Query a workflow status")
    query.add_argument("workflow_id")
    query.add_argument("--run-id", default="")
    query.add_argument("--query-type", default="get_candidate_status")

    approve = subparsers.add_parser("approve", help="Approve an evaluation expectation change")
    approve.add_argument("workflow_id")
    approve.add_argument("proposal_id")
    approve.add_argument("--run-id", default="")
    approve.add_argument("--notes", default="")

    reject = subparsers.add_parser("reject", help="Reject an evaluation expectation change")
    reject.add_argument("workflow_id")
    reject.add_argument("proposal_id")
    reject.add_argument("--run-id", default="")
    reject.add_argument("--notes", default="")

    return parser


async def start_edd_refinement_workflow(
    client,
    input_path: str | Path,
    *,
    workflow_id: Optional[str] = None,
    config: Optional[CadenceConfig] = None,
):
    """Start an EDD Refinement Workflow from a portable input document."""
    from common.preflight import resolve_and_validate_target_repository

    config = config or load_config()
    resolved_workflow_id = workflow_id or _default_workflow_id(input_path)

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
        run_id=resolved_workflow_id,
        lease_ttl=input_document.limits.get("eval_timeout_seconds", 1200),
    )
    if preflight.status != "success":
        raise EddRefinementInputError(
            f"preflight failed: {'; '.join(preflight.failed_conditions)}"
        )

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

    request = {
        "workflow_run_id": resolved_workflow_id,
        "profile": profile,
        "approval_timeout_seconds": 3600,
        "regression_stop_threshold": 3,
        "next_step_token_estimate": 0,
        "test_cases_path": str(input_document.test_cases),
        "coverage_metadata_property": input_document.coverage_metadata_property,
    }

    return await client.start_workflow(
        "EddRefinementWorkflow",
        preflight,
        request,
        **config.to_start_workflow_kwargs(resolved_workflow_id),
    )


async def _run_start(client, args: argparse.Namespace, config: CadenceConfig) -> int:
    execution = await start_edd_refinement_workflow(
        client, args.input_path, workflow_id=args.workflow_id, config=config
    )
    print(f"Started workflow_id={execution.workflow_id!r} run_id={execution.run_id!r}")
    return 0


async def _run_query(client, args: argparse.Namespace, config: CadenceConfig) -> int:
    try:
        status = await client.query_workflow(
            args.workflow_id,
            args.run_id,
            args.query_type,
            result_type=dict,
        )
    except EntityNotExistsError:
        print(f"Error: workflow not found: {args.workflow_id!r}", file=sys.stderr)
        return 1
    print(json.dumps(status))
    return 0


async def _run_approve(client, args: argparse.Namespace, config: CadenceConfig) -> int:
    await client.signal_workflow(
        args.workflow_id,
        args.run_id,
        "approve_evaluation_change",
        "approve",
        args.proposal_id,
        args.notes,
    )
    print(f"Sent approve decision={args.proposal_id!r} to workflow_id={args.workflow_id!r}")
    return 0


async def _run_reject(client, args: argparse.Namespace, config: CadenceConfig) -> int:
    await client.signal_workflow(
        args.workflow_id,
        args.run_id,
        "approve_evaluation_change",
        "reject",
        args.proposal_id,
        args.notes,
    )
    print(f"Sent reject decision={args.proposal_id!r} to workflow_id={args.workflow_id!r}")
    return 0


_COMMAND_HANDLERS = {
    "start": _run_start,
    "query": _run_query,
    "approve": _run_approve,
    "reject": _run_reject,
}


async def cli_main_async(
    argv: Sequence[str],
    *,
    client_factory: Optional[ClientFactory] = None,
    config: Optional[CadenceConfig] = None,
) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    resolved_config = config or load_config(
        domain=args.domain,
        task_list=args.task_list,
        cadence_target=args.target,
    )
    factory = client_factory or _default_client_factory
    handler = _COMMAND_HANDLERS[args.command]

    client = factory(resolved_config)
    async with client:
        try:
            return await handler(client, args, resolved_config)
        except EddRefinementInputError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1


def cli_main(argv: Optional[Sequence[str]] = None) -> int:
    return asyncio.run(cli_main_async(argv if argv is not None else sys.argv[1:]))


if __name__ == "__main__":
    sys.exit(cli_main())
