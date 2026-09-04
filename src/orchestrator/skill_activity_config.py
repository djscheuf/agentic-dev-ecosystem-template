import json
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Mapping


def _freeze(value: object) -> object:
    if isinstance(value, dict):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(item) for item in value)
    return value


@dataclass(frozen=True)
class SkillActivityConfig:
    skill_name: str
    output_path_key: str
    harness: Mapping[str, object]

    @classmethod
    def load(cls, config_path: Path) -> "SkillActivityConfig":
        safe_path = config_path.name
        try:
            content = config_path.read_text()
        except FileNotFoundError as exc:
            raise ValueError(f"missing_file: {safe_path}") from exc
        except OSError as exc:
            raise ValueError(f"unreadable_file: {safe_path}") from exc
        try:
            data = json.loads(content)
        except json.JSONDecodeError as exc:
            raise ValueError(f"malformed_json: {safe_path}") from exc
        if not isinstance(data, dict):
            raise ValueError("invalid_type: root")
        activity = data.get("activity")
        if not isinstance(activity, dict):
            raise ValueError("invalid_type: activity")
        for field_name in ("skill_name", "output_path_key"):
            if field_name not in activity:
                raise ValueError(f"missing_field: activity.{field_name}")
            if not isinstance(activity[field_name], str) or not activity[field_name].strip():
                raise ValueError(f"invalid_value: activity.{field_name}")
        harness = data.get("harness")
        if not isinstance(harness, dict):
            raise ValueError("invalid_type: harness")
        return cls(
            skill_name=activity["skill_name"],
            output_path_key=activity["output_path_key"],
            harness=_freeze(harness),
        )
