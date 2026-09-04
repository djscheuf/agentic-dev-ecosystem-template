from cadence import Registry, activity, workflow


def test_registry_supports_named_workflow_class_registration():
    class CharacterizedWorkflow:
        @workflow.run
        async def run(self):
            return None

    registry = Registry()

    registered_type = registry.workflow(name="CharacterizedWorkflow")(CharacterizedWorkflow)

    assert registered_type is CharacterizedWorkflow
    assert set(registry._workflows) == {"CharacterizedWorkflow"}


def test_registry_supports_named_activity_registration():
    @activity.defn(name="characterized_activity")
    async def characterized_activity():
        return None

    registry = Registry()

    registered_type = registry.register_activity(characterized_activity)

    assert registered_type is None
    assert set(registry._activities) == {"characterized_activity"}
