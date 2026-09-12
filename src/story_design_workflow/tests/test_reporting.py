import json
from dataclasses import asdict

import pytest

from story_design_workflow.reporting import (
    StoryDesignReport,
    write_story_design_report,
)


def test_write_story_design_report(tmp_path):
    report = StoryDesignReport(
        design_path="docs/foo.design.json",
        plan_path="docs/foo.plan.json",
        final_status="passed",
        score=0.95,
    )

    output_path = write_story_design_report(report, report_root=tmp_path)

    assert output_path == "foo.story-design.report.json"
    report_file = tmp_path / output_path
    assert report_file.exists()
    assert json.loads(report_file.read_text()) == asdict(report)
