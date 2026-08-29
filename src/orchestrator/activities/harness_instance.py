"""The `Harness` instance shared by the four skill Activities.

Centralized here so swapping the default `DevinHarness` for an alternative
`Harness` implementation (e.g. a different agent CLI, or a test double wired
up for a real integration run) only requires changing this one module.

The active harness class can be overridden at process start-up by setting the
``STORY_ANALYSIS_HARNESS`` environment variable to a fully-qualified class name
(``module.path:ClassName``).  This is used by the integration/E2E test suite to
run a real Cadence worker without invoking the ``devin`` CLI.
"""

import os
from typing import Type

from ..devin_harness import DevinHarness
from ..harness import Harness


def _load_harness() -> Harness:
    spec = os.environ.get("STORY_ANALYSIS_HARNESS")
    if not spec:
        return DevinHarness()

    module_name, class_name = spec.rsplit(":", 1)
    module = __import__(module_name, fromlist=[class_name])
    cls: Type[Harness] = getattr(module, class_name)
    return cls()


HARNESS = _load_harness()
