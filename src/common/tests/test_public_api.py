def test_common_exports_stable_foundation_api():
    import common

    assert common.__all__ == [
        "DevinHarness",
        "DevinHarnessConfig",
        "Harness",
        "HarnessResult",
        "SkillActivity",
        "SkillActivityConfig",
        "SkillActivityError",
        "SkillActivityInput",
        "SkillActivityOutput",
        "WorkerSpec",
        "WorkflowModuleSpec",
    ]
