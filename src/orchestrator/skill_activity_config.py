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
        data = json.loads(config_path.read_text())
        activity = data["activity"]
        return cls(
            skill_name=activity["skill_name"],
            output_path_key=activity["output_path_key"],
            harness=_freeze(data["harness"]),
        )
