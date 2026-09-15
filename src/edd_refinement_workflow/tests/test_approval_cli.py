from edd_refinement_workflow.approval_cli import build_arg_parser


def test_approval_cli_accepts_workflow_run_and_proposal_ids() -> None:
    parser = build_arg_parser()

    args = parser.parse_args(
        [
            "approve",
            "workflow-1",
            "proposal-1",
            "--run-id",
            "run-1",
            "--notes",
            "looks good",
        ]
    )

    assert args.command == "approve"
    assert args.workflow_id == "workflow-1"
    assert args.proposal_id == "proposal-1"
    assert args.run_id == "run-1"
