"""The `Harness` instance shared by the four skill Activities.

Centralized here so swapping the default `DevinHarness` for an alternative
`Harness` implementation (e.g. a different agent CLI, or a test double wired
up for a real integration run) only requires changing this one module.
"""

from ..devin_harness import DevinHarness

HARNESS = DevinHarness()
