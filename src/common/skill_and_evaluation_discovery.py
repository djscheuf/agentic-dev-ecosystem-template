import dataclasses
from pathlib import Path

import yaml


@dataclasses.dataclass
class SkillDiscoveryResult:
    ok: bool
    skill_path: Path | None = None
    evaluation_path: Path | None = None
    provider: str | None = None
    reason: str = ""


class SkillAndEvaluationDiscovery:
    def discover(
        self,
        skill_name: str,
        evaluation_path: str,
        target_root: str,
    ) -> SkillDiscoveryResult:
        root = Path(target_root)
        skill_path = root / ".devin" / "skills" / skill_name
        eval_path = (root / evaluation_path).resolve()
        if not skill_path.exists():
            return SkillDiscoveryResult(
                ok=False, reason=f"skill not found: {skill_path}"
            )
        if not eval_path.exists():
            return SkillDiscoveryResult(
                ok=False, reason=f"evaluation config not found: {eval_path}"
            )

        try:
            with eval_path.open("r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
        except yaml.YAMLError as exc:
            return SkillDiscoveryResult(
                ok=False, reason=f"malformed evaluation config: {exc}"
            )

        if not isinstance(config, dict):
            return SkillDiscoveryResult(
                ok=False, reason="evaluation config must be a YAML mapping"
            )

        providers = config.get("providers")
        if not isinstance(providers, list):
            return SkillDiscoveryResult(
                ok=False, reason="evaluation config must declare a providers list"
            )

        provider_ids = []
        for item in providers:
            if isinstance(item, str):
                provider_ids.append(item)
            elif isinstance(item, dict):
                for key in ("id", "provider"):
                    if key in item and isinstance(item[key], str):
                        provider_ids.append(item[key])
                        break

        if len(provider_ids) == 0:
            return SkillDiscoveryResult(
                ok=False, reason="evaluation config must declare exactly one provider"
            )
        if len(provider_ids) > 1:
            return SkillDiscoveryResult(
                ok=False,
                reason=f"evaluation config must resolve exactly one provider, found {len(provider_ids)}",
            )

        return SkillDiscoveryResult(
            ok=True,
            skill_path=skill_path,
            evaluation_path=eval_path,
            provider=provider_ids[0],
        )
