from pathlib import Path

import yaml


def append_refinement_outcome(target_root, run_id: str, outcome: dict) -> None:
    """Append a deterministic outcome event to the current iteration's section
    of the run's refinement.yaml. The document is the workflow's append-only
    historical narrative; agentic skills (edd-plan/edd-do) own the plan and
    changes-made subsections, while deterministic activities record outcomes
    (accept, confirmed regression, revert, handoff) here. No-op when the run
    has no refinement.yaml (e.g. runs resumed from before it existed)."""
    path = Path(target_root) / ".process" / "edd" / run_id / "refinement.yaml"
    if not path.exists():
        return
    document = yaml.safe_load(path.read_text()) or {}
    iterations = document.setdefault("iterations", [])
    if not iterations:
        iterations.append({})
    section = iterations[-1]
    section.setdefault("outcomes", []).append(outcome)
    path.write_text(yaml.safe_dump(document, sort_keys=False))
