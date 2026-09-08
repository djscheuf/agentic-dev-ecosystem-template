"""Pure ``asyncio`` engine for the Story Design Workflow.

Contains all of the sequencing and decision logic for the design workflow:
1. audit current reality based on the incoming analysis;
2. design story implementation using the analysis and audit;
3. grade the resulting design;
4. succeed if the grade passes, fail otherwise.

This module never imports ``cadence`` so it can be unit tested directly with
plain async fakes.
"""

import logging
from dataclasses import dataclass
from typing import Awaitable, Callable, Optional

_module_logger = logging.getLogger(__name__)
if not _module_logger.handlers:
    _module_logger.addHandler(logging.NullHandler())


class ActivityFailure(RuntimeError):
    """Raised when a skill Activity exhausts its Cadence RetryPolicy."""


@dataclass(frozen=True)
class WorkflowResult:
    design_path: Optional[str]
    passed: bool
    final_status: str  # "passed" | "failed"
    score: Optional[float] = None


ExecuteAuditCurrentReality = Callable[[str], Awaitable[dict]]
ExecuteDesignStoryImplementation = Callable[[str, str], Awaitable[dict]]
ExecuteGradeStoryDesign = Callable[[str], Awaitable[dict]]


class StoryDesignEngine:
    def __init__(
        self,
        *,
        execute_audit_current_reality: ExecuteAuditCurrentReality,
        execute_design_story_implementation: ExecuteDesignStoryImplementation,
        execute_grade_story_design: ExecuteGradeStoryDesign,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        self._execute_audit_current_reality = execute_audit_current_reality
        self._execute_design_story_implementation = execute_design_story_implementation
        self._execute_grade_story_design = execute_grade_story_design
        self._logger = logger or _module_logger

    async def _run_audit_current_reality(self, analysis_path: str) -> str:
        self._logger.info("Auditing current reality for analysis %s", analysis_path)
        result = await self._execute_audit_current_reality(analysis_path)
        self._logger.info("Audit complete: %s", result["output_path"])
        return result["output_path"]

    async def _run_design_story_implementation(
        self, analysis_path: str, audit_path: str
    ) -> str:
        self._logger.info(
            "Designing story implementation for analysis %s and audit %s",
            analysis_path,
            audit_path,
        )
        result = await self._execute_design_story_implementation(analysis_path, audit_path)
        self._logger.info("Design complete: %s", result["output_path"])
        return result["output_path"]

    async def _run_grade_story_design(self, design_path: str) -> dict:
        self._logger.info("Grading design %s", design_path)
        result = await self._execute_grade_story_design(design_path)
        self._logger.info("Grade result: passed=%s score=%s", result["passed"], result["score"])
        return result

    async def run(self, analysis_path: str) -> WorkflowResult:
        self._logger.info("Starting story design for %s", analysis_path)
        try:
            audit_path = await self._run_audit_current_reality(analysis_path)
            design_path = await self._run_design_story_implementation(analysis_path, audit_path)
            grade = await self._run_grade_story_design(design_path)
        except ActivityFailure:
            self._logger.error("Activity failed after exhausting retries")
            return WorkflowResult(
                design_path=None,
                passed=False,
                final_status="failed",
                score=None,
            )

        if grade["passed"]:
            self._logger.info("Design grade passed; workflow complete")
            return WorkflowResult(
                design_path=design_path,
                passed=True,
                final_status="passed",
                score=grade.get("score"),
            )

        self._logger.info("Design grade did not pass; failing workflow")
        return WorkflowResult(
            design_path=design_path,
            passed=False,
            final_status="failed",
            score=grade.get("score"),
        )
