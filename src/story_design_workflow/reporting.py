import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass
class StoryDesignReport:
    design_path: str
    final_status: str
    analysis_path: Optional[str] = None
    plan_path: Optional[str] = None
    score: Optional[float] = None


def _report_filename(design_path: str) -> str:
    design = Path(design_path)
    if design.name.endswith(".design.json"):
        return f"{design.name[:-len('.design.json')]}.story-design.report.json"
    return "story-design.report.json"


def write_story_design_report(
    report: StoryDesignReport,
    report_root: Optional[Path] = None,
) -> str:
    root = report_root if report_root is not None else REPO_ROOT
    root.mkdir(parents=True, exist_ok=True)

    report_file = root / _report_filename(report.design_path)
    report_file.write_text(json.dumps(asdict(report), indent=2))

    try:
        return str(report_file.relative_to(root))
    except ValueError:
        return str(report_file)
