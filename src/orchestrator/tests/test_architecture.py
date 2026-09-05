import ast
from pathlib import Path


ORCHESTRATOR_ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_DOMAIN_TERMS = (
    "Story Analysis",
    "StoryAnalysis",
    "story_analysis",
    "extract_story_intent",
    "analyze_story",
    "grade_story_analysis",
    "repair_story_analysis",
    "extract-story-intent",
    "analyze-story",
    "grade-story-analysis",
    "repair-story-analysis",
)


def test_orchestrator_package_when_imports_analyzed_contains_only_generic_concerns():
    violations = []
    for path in ORCHESTRATOR_ROOT.glob("*.py"):
        source = path.read_text()
        tree = ast.parse(source)
        imports = [
            node.module
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module
        ]
        if any(module.startswith("story_analysis_workflow") for module in imports):
            violations.append(f"{path.name}: workflow package import")
        for term in FORBIDDEN_DOMAIN_TERMS:
            if term in source:
                violations.append(f"{path.name}: {term}")

    assert violations == []
