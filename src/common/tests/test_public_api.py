def test_common_exports_workflow_module_and_worker_specs():
    import common

    assert common.__all__ == ["WorkflowModuleSpec", "WorkerSpec"]
    assert common.WorkflowModuleSpec.__name__ == "WorkflowModuleSpec"
    assert common.WorkerSpec.__name__ == "WorkerSpec"
