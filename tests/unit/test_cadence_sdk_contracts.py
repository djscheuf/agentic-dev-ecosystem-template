from cadence import Registry, workflow


def test_registry_supports_named_workflow_class_registration():
    class CharacterizedWorkflow:
        @workflow.run
        async def run(self):
            return None

    registry = Registry()

    registered_type = registry.workflow(name="CharacterizedWorkflow")(CharacterizedWorkflow)

    assert registered_type is CharacterizedWorkflow
    assert set(registry._workflows) == {"CharacterizedWorkflow"}
