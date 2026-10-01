import re
from pathlib import Path


class GitCommitMessageBuilder:
    """Build a commit message for an accepted EDD candidate.

    Loads the target repository's ``.devin/skills/git-commit/SKILL.md`` and
    looks for a ``Template: <message>`` line.  If no template is found, falls
    back to a conventional commit message.
    """

    _TEMPLATE_PATTERN = re.compile(r"^[Tt]emplate:\s*(.+)$", re.MULTILINE)

    def __init__(self, repo_root: str | Path) -> None:
        self.repo_root = Path(repo_root)

    def _skill_path(self) -> Path:
        return self.repo_root / ".devin" / "skills" / "git-commit" / "SKILL.md"

    def _extract_template(self, text: str) -> str | None:
        match = self._TEMPLATE_PATTERN.search(text)
        if match:
            return match.group(1).strip()
        return None

    def build(self, candidate_id: str) -> str:
        skill_path = self._skill_path()
        if skill_path.exists():
            template = self._extract_template(skill_path.read_text(encoding="utf-8"))
            if template:
                return template.format(candidate_id=candidate_id)
        return f"feat(edd refinement): accept candidate {candidate_id}"
