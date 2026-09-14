from cadence import workflow


class EddRefinementWorkflow:
    @workflow.run
    async def run(self, preflight_result, request: dict):
        raise NotImplementedError
