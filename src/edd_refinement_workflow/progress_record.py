import json
from pathlib import Path


class ProgressRecordStore:
    def __init__(self, target_root: Path) -> None:
        self.target_root = Path(target_root)

    def _record_path(self, run_id: str) -> Path:
        return self.target_root / ".process" / "edd" / run_id / "progress.json"

    def create_or_resume(self, run_id: str, record: dict) -> dict:
        path = self._record_path(run_id)
        if path.exists():
            return json.loads(path.read_text())
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(record, indent=2, sort_keys=True))
        return record
