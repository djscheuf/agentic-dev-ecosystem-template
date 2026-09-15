import argparse
import asyncio
import json
from collections.abc import Sequence

from cadence.client import Client

from .signals import get_approval_status, send_approval_decision


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="edd-approval")
    parser.add_argument("--domain", default="edd-refinement")
    parser.add_argument("--target", default="localhost:7933")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for decision in ("approve", "reject"):
        command = subparsers.add_parser(decision)
        command.add_argument("workflow_id")
        command.add_argument("proposal_id")
        command.add_argument("--run-id", default="")
        command.add_argument("--notes", default="")
    status = subparsers.add_parser("status")
    status.add_argument("workflow_id")
    status.add_argument("--run-id", default="")
    return parser


async def cli_main_async(argv: Sequence[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    client = Client(domain=args.domain, target=args.target)
    if args.command == "status":
        status = await get_approval_status(client, args.workflow_id, run_id=args.run_id)
        print(json.dumps(status, indent=2, sort_keys=True))
        return 0
    await send_approval_decision(
        client,
        args.workflow_id,
        args.proposal_id,
        args.command,
        args.notes,
        run_id=args.run_id,
    )
    print(
        f"Sent {args.command} for proposal_id={args.proposal_id!r} "
        f"to workflow_id={args.workflow_id!r}"
    )
    return 0


def cli_main(argv: Sequence[str] | None = None) -> int:
    return asyncio.run(cli_main_async(argv))


if __name__ == "__main__":
    raise SystemExit(cli_main())
