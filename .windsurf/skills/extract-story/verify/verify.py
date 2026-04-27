# verify/verify-extract-story.py

import json, sys, jsonschema

from exceptions import StoryVerificationError


SCHEMA = json.load(open("schema/user-story.schema.json"))

VALID_CRITERION_TYPES = {"Functional", "Non-functional", "Happy path", "Error handling","Edge Case"}
VALID_RISK_LEVELS = {"Low", "Medium", "High"}
ACCEPTED_STORY_POINTS = {1, 2, 3, 5, 8, 13, 21}


def verify_structure(story_path: str) -> None:
    story = json.load(open(story_path))
    failures = []
    
    try:
        jsonschema.validate(story, SCHEMA)
    except jsonschema.ValidationError as e:
        failures.append(f"Schema validation failed: {e.message}")
    
    if failures:
        raise StoryVerificationError(
            "Story failed structure verification:\n" + "\n".join(failures)
        )


def verify_story_completeness(story_path: str) -> None:
    story = json.load(open(story_path))
    failures = []
    
    required_fields = ["title", "story", "target_persona", "capability_breakdown", "acceptance_criteria"]
    for field in required_fields:
        if field not in story or not story[field]:
            failures.append(f"Missing required field: '{field}'")
    
    if "story" in story:
        story_obj = story["story"]
        required_story_fields = ["as_a", "i_want", "so_that"]
        for field in required_story_fields:
            if field not in story_obj or not story_obj[field]:
                failures.append(f"Story missing required field: '{field}'")
    
    if "target_persona" in story:
        persona = story["target_persona"]
        if "name" not in persona or not persona["name"]:
            failures.append("Target persona missing 'name'")
        if "role" not in persona or not persona["role"]:
            failures.append("Target persona missing 'role'")
    
    if "acceptance_criteria" in story:
        criteria_list = story["acceptance_criteria"]
        if not isinstance(criteria_list, list) or len(criteria_list) == 0:
            failures.append("Acceptance criteria must be a non-empty list")
        else:
            for idx, criterion in enumerate(criteria_list):
                if "criterion" not in criterion or not criterion["criterion"]:
                    failures.append(f"Acceptance criterion {idx} missing 'criterion' field")
                if "type" not in criterion or not criterion["type"]:
                    failures.append(f"Acceptance criterion {idx} missing 'type' field")
                elif criterion["type"] not in VALID_CRITERION_TYPES:
                    failures.append(
                        f"Acceptance criterion {idx} has invalid type '{criterion['type']}'. "
                        f"Must be one of: {', '.join(VALID_CRITERION_TYPES)}"
                    )
    
    if failures:
        raise StoryVerificationError(
            "Story failed completeness verification:\n" + "\n".join(failures)
        )


def verify_consistency(story_path: str) -> None:
    story = json.load(open(story_path))
    failures = []
    
    if "acceptance_criteria" in story and "target_persona" in story:
        persona_name = story["target_persona"].get("name", "")
        criteria_list = story["acceptance_criteria"]
        
        target_persona_served = False
        for idx, criterion in enumerate(criteria_list):
            persona_served = criterion.get("persona_served", "")
            if persona_served == persona_name:
                target_persona_served = True
        
        if not target_persona_served:
            failures.append(
                f"Target persona '{persona_name}' is not served by any acceptance criterion. "
                f"At least one criterion must have persona_served matching the target persona."
            )
    
    if "complexity" in story:
        complexity = story["complexity"]
        if "risk_level" in complexity:
            risk = complexity["risk_level"]
            if risk not in VALID_RISK_LEVELS:
                failures.append(
                    f"Risk level '{risk}' is invalid. "
                    f"Must be one of: {', '.join(VALID_RISK_LEVELS)}"
                )
        
        if "story_points" in complexity:
            points = complexity["story_points"]
            if not isinstance(points, (int, float)) or points <= 0:
                failures.append(
                    f"Story points must be a positive number, got: {points}"
                )
            elif points not in ACCEPTED_STORY_POINTS:
                failures.append(
                    f"Story points '{points}' is not a valid Fibonacci value. "
                    f"Accepted values: {sorted(ACCEPTED_STORY_POINTS)}"
                )
    
    if failures:
        raise StoryVerificationError(
            "Story failed consistency verification:\n" + "\n".join(failures)
        )


if __name__ == "__main__":
    sentinel_path = sys.argv[1]
    sentinel = json.load(open(sentinel_path))
    verify_params = sentinel.get("verify_params", {})
    story_path = verify_params.get("extracted_story_path")
    
    if not story_path:
        raise StoryVerificationError("verify_params missing 'extracted_story_path'")
    
    verify_structure(story_path)
    verify_story_completeness(story_path)
    verify_consistency(story_path)
