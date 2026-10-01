import json
import re
from pathlib import Path


class SchemaVersionMismatch(Exception):
    pass


_REDACTED = "[REDACTED]"
_CREDENTIAL_KEYWORDS = {"aws", "credential", "secret", "token", "password", "key", "private"}
_ENV_VAR_PATTERN = re.compile(r"\$\{[A-Z_][A-Z0-9_]*\}")
_PATH_PREFIXES = ("/", "~", "./")


class ProgressRecordSerializer:
    @classmethod
    def for_v5(cls):
        return cls(
            schema_version=5,
            allowed_fields={
                "schema_version",
                "run_id",
                "budgets",
                "logical_iteration_count",
                "cumulative_token_usage",
                "consecutive_confirmed_regressions",
                "pending_evidence_flags",
                "attempts",
                "human_handoff_records",
                "iteration_start_baseline",
                "modification_scope",
                "scope_violations",
            },
        )

    def __init__(self, schema_version: int, allowed_fields: set) -> None:
        self.schema_version = schema_version
        self.allowed_fields = allowed_fields

    def _is_credential_path(self, value: str) -> bool:
        if not any(value.startswith(prefix) for prefix in _PATH_PREFIXES):
            return False
        return any(keyword in value.lower() for keyword in _CREDENTIAL_KEYWORDS)

    def _redact(self, value):
        if isinstance(value, dict):
            return {k: self._redact(v) for k, v in value.items()}
        if isinstance(value, list):
            return [self._redact(v) for v in value]
        if not isinstance(value, str):
            return value
        if _ENV_VAR_PATTERN.search(value) or self._is_credential_path(value):
            return _REDACTED
        return value

    def serialize(self, record: dict) -> dict:
        if record.get("schema_version") != self.schema_version:
            raise SchemaVersionMismatch
        return {
            k: self._redact(v)
            for k, v in record.items()
            if k in self.allowed_fields
        }

    def deserialize(self, record: dict) -> dict:
        return self.serialize(record)


class ProgressRecordAlreadyExists(Exception):
    pass


class ProgressRecordFactory:
    def __init__(self, store) -> None:
        self.store = store

    def derive_run_id(self, workflow_run_id: str, starting_revision: str) -> str:
        return f"{workflow_run_id}-{starting_revision[:7]}"

    def create(self, run_id: str, record: dict) -> dict:
        if self.store._record_path(run_id).exists():
            raise ProgressRecordAlreadyExists
        return self.store.create_or_resume(run_id, record)

    def create_or_resume(self, run_id: str, record: dict) -> dict:
        return self.store.create_or_resume(run_id, record)


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

    def save(self, run_id: str, record: dict) -> None:
        path = self._record_path(run_id)
        path.write_text(json.dumps(record, indent=2, sort_keys=True))
