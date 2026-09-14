import dataclasses
from pathlib import Path


@dataclasses.dataclass
class SkillDiscoveryResult:
    ok: bool
    skill_path: Path | None = None
    evaluation_path: Path | None = None


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
        if not skill_path.exists() or not eval_path.exists():
            return SkillDiscoveryResult(ok=False)
        return SkillDiscoveryResult(
            ok=True, skill_path=skill_path, evaluation_path=eval_path
        )
