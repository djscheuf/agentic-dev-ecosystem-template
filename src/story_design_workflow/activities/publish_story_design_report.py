import json
from pathlib import Path
from typing import Optional

from cadence import activity

REPO_ROOT = Path(__file__).resolve().parents[3]


def _report_filename(design_path: str) -> str:
    design = Path(design_path)
    if design.name.endswith(".design.json"):
        return f"{design.name[:-len('.design.json')]}.story-design.report.json"
    return "story-design.report.json"


@activity.defn(name="publish_story_design_report")
async def publish_story_design_report(
    design_path: str,
    plan_path: Optional[str] = None,
    report_root: Optional[str] = None,
) -> dict:
    root = Path(report_root) if report_root else REPO_ROOT
    root.mkdir(parents=True, exist_ok=True)

    report_file = root / _report_filename(design_path)
    payload = {
        "design_path": design_path,
        "plan_path": plan_path,
        "final_status": "passed" if plan_path else "failed",
    }
    report_file.write_text(json.dumps(payload, indent=2))

    try:
        output_path = str(report_file.relative_to(root))
    except ValueError:
        output_path = str(report_file)

    return {"output_path": output_path, "design_path": design_path, "plan_path": plan_path}
