import dataclasses
import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any


class EddRefinementInputError(ValueError):
    """The input document is malformed, missing required fields, or violates a contract."""


@dataclasses.dataclass
class EddRefinementInput:
    schema_version: int
    input_path: Path
    input_parent: Path
    skill_folder: Path
    eval_config: Path
    test_command: list[str]
    inspect_command: list[str]
    test_cases: Path
    coverage_metadata_property: str
    modification_scope: list[Path]
    limits: dict[str, Any]
    related_content: list[Path] = dataclasses.field(default_factory=list)

    _REQUIRED_FIELDS = (
        "skill_folder",
        "eval_config",
        "test_command",
        "inspect_command",
        "test_cases",
        "coverage_metadata_property",
        "modification_scope",
        "limits",
    )

    @classmethod
    def from_path(cls, input_path: str | Path) -> "EddRefinementInput":
        input_path = Path(input_path).resolve()
        input_parent = input_path.parent

        try:
            with input_path.open("r", encoding="utf-8") as f:
                raw = json.load(f)
        except json.JSONDecodeError as exc:
            raise EddRefinementInputError("malformed JSON input") from exc

        if not isinstance(raw, dict):
            raise EddRefinementInputError("input document must be a JSON object")

        for field_name in cls._REQUIRED_FIELDS:
            if field_name not in raw or raw[field_name] is None:
                raise EddRefinementInputError(f"missing required field: {field_name}")

        schema_version = raw.get("schema_version", 1)

        limits = raw["limits"]
        if not isinstance(limits, dict):
            raise EddRefinementInputError("limits must be a JSON object")

        eval_timeout = limits.get("eval_timeout_seconds")
        if not isinstance(eval_timeout, int) or eval_timeout <= 0:
            raise EddRefinementInputError(
                "limits.eval_timeout_seconds must be a positive integer"
            )

        if not any(
            isinstance(limits.get(k), int) and limits.get(k, 0) > 0
            for k in ("max_iterations", "max_tokens")
        ):
            raise EddRefinementInputError(
                "limits must include a positive max_iterations or max_tokens"
            )

        coverage_metadata_property = raw["coverage_metadata_property"]
        if not isinstance(coverage_metadata_property, str) or not coverage_metadata_property.strip():
            raise EddRefinementInputError(
                "coverage_metadata_property must be a non-empty dotted string"
            )

        def _resolve(value: str) -> Path:
            return (input_parent / value).resolve()

        def _resolve_list(value: Any) -> list[Path]:
            if not isinstance(value, Sequence) or isinstance(value, str):
                raise EddRefinementInputError(
                    "path list must contain non-empty strings"
                )
            resolved = []
            for item in value:
                if not isinstance(item, str) or not item:
                    raise EddRefinementInputError(
                        "path list must contain non-empty strings"
                    )
                resolved.append(_resolve(item))
            return resolved

        def _command_list(value: Any, name: str) -> list[str]:
            if not isinstance(value, Sequence) or isinstance(value, str) or not value:
                raise EddRefinementInputError(f"{name} must be a non-empty list of strings")
            if not all(isinstance(item, str) for item in value):
                raise EddRefinementInputError(f"{name} must contain only strings")
            return list(value)

        modification_scope = _resolve_list(raw["modification_scope"])
        if not modification_scope:
            raise EddRefinementInputError("modification_scope must not be empty")

        test_command = _command_list(raw["test_command"], "test_command")
        inspect_command = _command_list(raw["inspect_command"], "inspect_command")

        related = raw.get("related_content", [])
        if related is None:
            related = []

        return cls(
            schema_version=schema_version,
            input_path=input_path,
            input_parent=input_parent,
            skill_folder=_resolve(raw["skill_folder"]),
            eval_config=_resolve(raw["eval_config"]),
            test_command=test_command,
            inspect_command=inspect_command,
            test_cases=_resolve(raw["test_cases"]),
            coverage_metadata_property=coverage_metadata_property,
            modification_scope=modification_scope,
            limits=limits,
            related_content=_resolve_list(related) if related else [],
        )
