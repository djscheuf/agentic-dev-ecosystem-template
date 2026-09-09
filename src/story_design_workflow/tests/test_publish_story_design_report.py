import json
from pathlib import Path

import pytest

from story_design_workflow.activities.publish_story_design_report import (
    publish_story_design_report,
)


@pytest.mark.asyncio
async def test_publish_story_design_report_writes_file(tmp_path):
    report = await publish_story_design_report(
        "docs/foo.design.json",
        "docs/foo.plan.json",
        report_root=str(tmp_path),
    )

    assert report["output_path"] == "foo.story-design.report.json"
    report_file = tmp_path / report["output_path"]
    assert report_file.exists()

    content = json.loads(report_file.read_text())
    assert content["design_path"] == "docs/foo.design.json"
    assert content["plan_path"] == "docs/foo.plan.json"
    assert content["final_status"] == "passed"


@pytest.mark.asyncio
async def test_publish_story_design_report_marks_failed_when_no_plan(tmp_path):
    report = await publish_story_design_report(
        "docs/foo.design.json",
        None,
        report_root=str(tmp_path),
    )

    assert report["output_path"] == "foo.story-design.report.json"
    report_file = tmp_path / report["output_path"]
    assert report_file.exists()

    content = json.loads(report_file.read_text())
    assert content["plan_path"] is None
    assert content["final_status"] == "failed"
