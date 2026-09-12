"""``story-design-cli`` -- start the Story Design Workflow and register its
Cadence domain, without requiring the ``cadence`` CLI binary.
"""

import argparse
import asyncio
import json
import sys
from datetime import timedelta
from typing import Callable, Optional, Sequence

from cadence.client import Client
from cadence.api.v1 import service_domain_pb2

from .config import CadenceConfig, load_config
from .starter import start_story_design_workflow
from .workflow_logger import client_log_context, get_client_logger

ClientFactory = Callable[[CadenceConfig], Client]


def _default_client_factory(config: CadenceConfig) -> Client:
    return Client(domain=config.domain, target=config.cadence_target)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="story-design-cli")
    parser.add_argument("--domain")
    parser.add_argument("--task-list")
    parser.add_argument("--target")
    subparsers = parser.add_subparsers(dest="command", required=True)

    start = subparsers.add_parser("start", help="Start a Story Design Workflow execution")
    start.add_argument("analysis_path")
    start.add_argument("--workflow-id")

    register_domain = subparsers.add_parser("register-domain", help="Register the workflow's Cadence domain")
    register_domain.add_argument("--retention-days", type=int, default=1)

    return parser


async def _run_start(client, args: argparse.Namespace, config: CadenceConfig) -> int:
    execution = await start_story_design_workflow(
        client,
        args.analysis_path,
        workflow_id=args.workflow_id,
        config=config,
    )
    print(f"Started workflow_id={execution.workflow_id!r} run_id={execution.run_id!r}")
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
