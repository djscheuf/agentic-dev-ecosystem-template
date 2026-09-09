from pathlib import Path
from typing import Optional

from cadence import activity


@activity.defn(name="publish_story_design_report")
async def publish_story_design_report(design_path: str, plan_path: Optional[str] = None) -> dict:
    design = Path(design_path)
    if design.name.endswith(".design.json"):
        report_path = design.with_name(
            f"{design.name[:-len('.design.json')]}.story-design.report.json"
        )
    else:
        report_path = design.with_name("story-design.report.json")
    return {"output_path": str(report_path), "design_path": design_path, "plan_path": plan_path}
