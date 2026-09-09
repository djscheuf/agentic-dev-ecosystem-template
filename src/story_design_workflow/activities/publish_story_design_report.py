from pathlib import Path
from typing import Optional

from cadence import activity

from ..reporting import StoryDesignReport, write_story_design_report


@activity.defn(name="publish_story_design_report")
async def publish_story_design_report(
    design_path: str,
    plan_path: Optional[str] = None,
    score: Optional[float] = None,
    analysis_path: Optional[str] = None,
    report_root: Optional[str] = None,
) -> dict:
    report = StoryDesignReport(
        design_path=design_path,
        plan_path=plan_path,
        final_status="passed" if plan_path else "failed",
        score=score,
        analysis_path=analysis_path,
    )
    output_path = write_story_design_report(
        report,
        report_root=Path(report_root) if report_root else None,
    )
    return {
        "output_path": output_path,
        "design_path": design_path,
        "plan_path": plan_path,
    }
