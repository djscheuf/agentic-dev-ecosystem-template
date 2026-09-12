"""Shared fixtures for the top-level test suite."""

import pytest
from cadence.client import Client


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "needs_cadence: mark test as requiring a Cadence server on localhost:7833",
    )


@pytest.fixture
async def cadence_client():
    async with Client(domain="story-analysis", target="localhost:7833") as client:
        yield client
