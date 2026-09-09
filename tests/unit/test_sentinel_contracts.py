from pathlib import Path


REPO_ROOT = Path(__file__).parents[2]
SKILLS_ROOT = REPO_ROOT / ".devin" / "skills"


def test_skill_contracts_all_verifiable_skills_retain_colocated_sentinels():
    verify_scripts = sorted(SKILLS_ROOT.glob("*/verify.sh"))

    violations = []
    for verify_script in verify_scripts:
        instructions = (verify_script.parent / "SKILL.md").read_text()
        verification = verify_script.read_text()
        if "<input_parent>/.process/" not in instructions:
            violations.append(f"{verify_script.parent.name}: missing co-located path")
        if "must not be removed after verification" not in instructions:
            violations.append(f"{verify_script.parent.name}: missing retention requirement")
        if 'rm -f "$sentinel_path"' in verification:
            violations.append(f"{verify_script.parent.name}: deletes sentinel")

    assert violations == []
