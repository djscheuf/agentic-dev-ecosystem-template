"""Integration test configuration for the Story Analysis Workflow example."""


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "needs_cadence: mark test as requiring a Cadence server on localhost:7833",
    )
