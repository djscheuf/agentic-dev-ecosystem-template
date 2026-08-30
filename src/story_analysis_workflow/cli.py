"""`story-analysis-cli` -- start/signal/query the Story Analysis Workflow and
register its Cadence domain, without requiring the `cadence` CLI binary.

See `docs/reqs/workflow-orchestration/client-api-usage.md` for usage.
"""

import argparse
import asyncio
import json
import sys
from datetime import timedelta
from typing import Callable, Optional, Sequence

from cadence.client import Client
from cadence.error import EntityNotExistsError
from cadence.api.v1 import service_domain_pb2

from .config import CadenceConfig, load_config
from .queries import get_status
from .signals import send_human_response
from .starter import start_story_analysis_workflow

ClientFactory = Callable[[CadenceConfig], Client]


def _default_client_factory(config: CadenceConfig) -> Client:
    return Client(domain=config.domain, target=config.cadence_target)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="story-analysis-cli")
    parser.add_argument("--domain")
    parser.add_argument("--task-list")
    parser.add_argument("--target")
    subparsers = parser.add_subparsers(dest="command", required=True)

    start = subparsers.add_parser("start", help="Start a Story Analysis Workflow execution")
    start.add_argument("story_document")
    start.add_argument("--workflow-id")
    start.add_argument("--max-attempts", type=int)
    start.add_argument("--escalation-timeout-seconds", type=int)

    signal = subparsers.add_parser("signal", help="Send the human_response Signal")
    signal.add_argument("workflow_id")
    signal.add_argument("decision", choices=["retry", "accept", "abort"])
    signal.add_argument("--notes", default="")
    signal.add_argument("--run-id", default="")

    query = subparsers.add_parser("query", help="Query the get_status Query")
    query.add_argument("workflow_id")
    query.add_argument("--run-id", default="")

    register_domain = subparsers.add_parser("register-domain", help="Register the workflow's Cadence domain")
    register_domain.add_argument("--retention-days", type=int, default=1)

    return parser


async def _run_start(client, args: argparse.Namespace, config: CadenceConfig) -> int:
    engine_config = {}
    if args.max_attempts is not None:
        engine_config["max_attempts"] = args.max_attempts
    if args.escalation_timeout_seconds is not None:
        engine_config["escalation_timeout_seconds"] = args.escalation_timeout_seconds

    execution = await start_story_analysis_workflow(
        client,
        args.story_document,
        workflow_id=args.workflow_id,
        config=config,
        **engine_config,
    )
    print(f"Started workflow_id={execution.workflow_id!r} run_id={execution.run_id!r}")
    return 0


async def _run_signal(client, args: argparse.Namespace, config: CadenceConfig) -> int:
    await send_human_response(client, args.workflow_id, args.decision, args.notes, run_id=args.run_id)
    print(f"Sent human_response decision={args.decision!r} to workflow_id={args.workflow_id!r}")
    return 0


async def _run_query(client, args: argparse.Namespace, config: CadenceConfig) -> int:
    try:
        status = await get_status(client, args.workflow_id, run_id=args.run_id)
    except EntityNotExistsError as exc:
        print(
            f"Error: workflow not found: {args.workflow_id!r}",
            file=sys.stderr,
        )
        if args.run_id:
            print(f"       run_id: {args.run_id!r}", file=sys.stderr)
        print(
            "       Verify you are using the workflow_id returned by the start command.",
            file=sys.stderr,
        )
        return 1
    print(json.dumps(status))
    return 0


async def _run_register_domain(client, args: argparse.Namespace, config: CadenceConfig) -> int:
    request = service_domain_pb2.RegisterDomainRequest(
        name=config.domain,
        workflow_execution_retention_period=timedelta(days=args.retention_days),
    )
    await client.domain_stub.RegisterDomain(request)
    print(f"Registered domain={config.domain!r} retention_days={args.retention_days}")
    return 0


_COMMAND_HANDLERS = {
    "start": _run_start,
    "signal": _run_signal,
    "query": _run_query,
    "register-domain": _run_register_domain,
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
        return await handler(client, args, resolved_config)


def cli_main(argv: Optional[Sequence[str]] = None) -> int:
    return asyncio.run(cli_main_async(argv if argv is not None else sys.argv[1:]))


if __name__ == "__main__":
    sys.exit(cli_main())
