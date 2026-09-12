"""Ping test for the local SQLite-backed Cadence server.

Verifies that the Cadence Python client can reach the gRPC frontend on
localhost:7833 and that the 'story-analysis' domain is registered.

Run with the cadence-python-client package installed:
    pip install cadence-python-client
    python docker/cadence-ping.py
"""

import asyncio
import sys

from cadence.client import Client
from cadence.api.v1 import service_domain_pb2

CADENCE_TARGET = "localhost:7833"
DOMAIN = "story-analysis"


async def main() -> int:
    async with Client(domain=DOMAIN, target=CADENCE_TARGET) as client:
        request = service_domain_pb2.DescribeDomainRequest(name=DOMAIN)
        response = await client.domain_stub.DescribeDomain(request)

    domain = response.domain
    print(f"Host:            {CADENCE_TARGET}")
    print(f"Domain:          {domain.name}")
    print(f"Domain ID:       {domain.id}")
    print(f"Status:          {domain.status}")
    print(f"Retention (s):   {domain.workflow_execution_retention_period.seconds}")
    print("Python client connection OK.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(asyncio.run(main()))
    except Exception as exc:  # noqa: BLE001
        print(f"Connection failed: {exc}", file=sys.stderr)
        sys.exit(1)
