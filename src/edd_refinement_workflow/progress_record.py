import json
from pathlib import Path


class SchemaVersionMismatch(Exception):
    pass


class ProgressRecordSerializer:
    def __init__(self, schema_version: int, allowed_fields: set) -> None:
        self.schema_version = schema_version
        self.allowed_fields = allowed_fields

    def serialize(self, record: dict) -> dict:
        if record.get("schema_version") != self.schema_version:
            raise SchemaVersionMismatch
        return {k: v for k, v in record.items() if k in self.allowed_fields}


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
