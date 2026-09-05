"""Helpers for starting a worker subprocess during integration tests."""

import asyncio
import json
import os
import sys
from contextlib import asynccontextmanager


@asynccontextmanager
async def run_worker(
    *,
    harness_class: str = "tests.fake_harness:FakeHarness",
    grade_results: list | None = None,
    fail_skills: list | None = None,
    ready_timeout: float = 30.0,
):
    """Start ``python -m orchestrator.worker`` in a subprocess and yield it.

    The worker is configured to use ``tests.fake_harness.FakeHarness`` so the
    integration tests exercise the real Cadence server and Python workflow
    code without invoking the ``devin`` CLI.
    """
    env = os.environ.copy()
    pythonpath_parts = ["src"]
    if env.get("PYTHONPATH"):
        pythonpath_parts.append(env["PYTHONPATH"])
    env["PYTHONPATH"] = ":".join(pythonpath_parts)
    env["PYTHONUNBUFFERED"] = "1"
    env["STORY_ANALYSIS_HARNESS"] = harness_class
    if grade_results is not None:
        env["STORY_ANALYSIS_GRADE_RESULTS"] = json.dumps(grade_results)
    if fail_skills is not None:
        env["STORY_ANALYSIS_FAIL_SKILLS"] = json.dumps(fail_skills)

    process = await asyncio.create_subprocess_exec(
        sys.executable,
        "-m",
        "orchestrator.worker",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=env,
    )

    try:
        ready_line = await asyncio.wait_for(
            process.stdout.readline(),
            timeout=ready_timeout,
        )
        if not ready_line:
            stderr = ""
            if process.stderr:
                stderr = (await process.stderr.read()).decode("utf-8", errors="replace")
            raise RuntimeError(f"Worker exited before becoming ready. stderr:\n{stderr}")
        yield process
    finally:
        process.terminate()
        try:
            await asyncio.wait_for(process.wait(), timeout=5.0)
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
