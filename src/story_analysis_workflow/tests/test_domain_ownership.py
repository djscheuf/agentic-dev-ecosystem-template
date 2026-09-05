from importlib import import_module


def test_story_analysis_package_owns_domain_behavior():
    expected_symbols = {
        "story_analysis_workflow.workflow": "StoryAnalysisWorkflow",
        "story_analysis_workflow.story_analysis_engine": "StoryAnalysisEngine",
        "story_analysis_workflow.escalation": "HumanResponse",
        "story_analysis_workflow.grade_repair": "evaluate_grade_repair",
        "story_analysis_workflow.grade_scoring": "score_analysis_grade",
        "story_analysis_workflow.workflow_logger": "get_workflow_logger",
    }

    imported_symbols = {
        module_name: getattr(import_module(module_name), symbol_name)
        for module_name, symbol_name in expected_symbols.items()
    }

    assert set(imported_symbols) == set(expected_symbols)
