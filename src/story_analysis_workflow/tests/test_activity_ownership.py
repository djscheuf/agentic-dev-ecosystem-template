from pathlib import Path


ACTIVITY_NAMES = (
    "extract_story_intent",
    "analyze_story",
    "grade_story_analysis",
    "repair_story_analysis",
)


def test_story_analysis_package_owns_activities_and_configuration():
    activities_dir = Path(__file__).parents[1] / "activities"

    owned_files = {
        path.name
        for activity_name in ACTIVITY_NAMES
        for path in (
            activities_dir / f"{activity_name}.py",
            activities_dir / f"{activity_name}.config.json",
        )
        if path.is_file()
    }

    assert owned_files == {
        f"{activity_name}{suffix}"
        for activity_name in ACTIVITY_NAMES
        for suffix in (".py", ".config.json")
    }
