import dataclasses
import json
from pathlib import Path


class BaselineResultError(Exception):
    pass


@dataclasses.dataclass
class BaselineResult:
    passing: int
    failing: int
    total: int
    percentage: float
    coverage: dict
    failures: list
    duration: float
    outcome: str


_REQUIRED_FIELDS = {
    "passing",
    "failing",
    "total",
    "percentage",
    "coverage",
    "failures",
    "duration",
    "outcome",
}


class BaselineResultParser:
    def parse(self, raw: dict) -> BaselineResult:
        missing = _REQUIRED_FIELDS - raw.keys()
        if missing:
            raise BaselineResultError(
                f"missing baseline result fields: {sorted(missing)}"
            )
        return BaselineResult(
            **{field: raw[field] for field in _REQUIRED_FIELDS}
        )


class BaselineResultArtifactWriter:
    def __init__(self, target_root) -> None:
        self.target_root = Path(target_root)

    def write(self, run_id: str, result: BaselineResult) -> str:
        path = self.target_root / ".process" / "edd" / run_id / "baseline.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(dataclasses.asdict(result), indent=2, sort_keys=True)
        )
        return str(path.relative_to(self.target_root))
