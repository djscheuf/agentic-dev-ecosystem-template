import os
from typing import Type

from common.devin_harness import DevinHarness
from common.harness import Harness


def _load_harness() -> Harness:
    spec = os.environ.get("STORY_ANALYSIS_HARNESS")
    if not spec:
        return DevinHarness()

    module_name, class_name = spec.rsplit(":", 1)
    module = __import__(module_name, fromlist=[class_name])
    cls: Type[Harness] = getattr(module, class_name)
    return cls()


HARNESS = _load_harness()
