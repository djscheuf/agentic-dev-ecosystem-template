"""Pure ``asyncio`` engine for the Story Design Workflow.

Contains all of the sequencing and decision logic for the design workflow:
1. validate the incoming analysis source document;
2. audit current reality based on the incoming analysis;
3. validate the audit artifact;
4. design story implementation using the analysis and audit;
5. validate the design artifact;
6. grade the resulting design;
7. succeed if the grade passes, fail otherwise.

This module never imports ``cadence`` so it can be unit tested directly with
plain async fakes.
"""

import logging
from dataclasses import dataclass
from typing import Awaitable, Callable, Optional

from .handoff_validation import GuardrailRule, HandoffValidationResult
from .source_document_validation import SourceDocumentValidationResult, SourceDocumentValidationRule

_module_logger = logging.getLogger(__name__)
if not _module_logger.handlers:
    _module_logger.addHandler(logging.NullHandler())


class ActivityFailure(RuntimeError):
    """Raised when a skill Activity exhausts its Cadence RetryPolicy."""


AUDIT_SCHEMA_PATH = ".devin/skills/audit-current-reality/schema/audit.schema.json"
DESIGN_SCHEMA_PATH = ".devin/skills/design-story-implementation/schema/design.schema.json"
PLAN_SCHEMA_PATH = ".devin/skills/draft-implementation-plan/schema/plan.schema.json"


@dataclass(frozen=True)
class WorkflowResult:
    design_path: Optional[str]
    passed: bool
    final_status: str  # "passed" | "failed" | "validation_failed" | "handoff_failed"
    score: Optional[float] = None
    validation_rule: Optional[SourceDocumentValidationRule] = None
    handoff_rule: Optional[GuardrailRule] = None
    plan_path: Optional[str] = None
    report_path: Optional[str] = None


ValidateSourceDocument = Callable[[Optional[str]], Awaitable[SourceDocumentValidationResult]]
ValidateHandoff = Callable[[str, str], Awaitable[HandoffValidationResult]]
ExecuteAuditCurrentReality = Callable[[str], Awaitable[dict]]
ExecuteDesignStoryImplementation = Callable[[str, str], Awaitable[dict]]
ExecuteGradeStoryDesign = Callable[[str], Awaitable[dict]]
ExecuteDraftImplementationPlan = Callable[[str], Awaitable[dict]]
ExecutePublishStoryDesignReport = Callable[[str, Optional[str], Optional[float], Optional[str]], Awaitable[dict]]


async def _valid_source_document(_analysis_path: Optional[str]) -> SourceDocumentValidationResult:
    return SourceDocumentValidationResult(True, SourceDocumentValidationRule.VALID)


async def _valid_handoff(_output_path: str, _schema_path: str) -> HandoffValidationResult:
    return HandoffValidationResult(
        valid=True,
        ambiguity=False,
        rule=GuardrailRule.PASSED,
        artifact_path=_output_path,
        schema_path=_schema_path,
    )


class StoryDesignEngine:
    def __init__(
        self,
        *,
        validate_source_document: Optional[ValidateSourceDocument] = None,
        validate_handoff: Optional[ValidateHandoff] = None,
        execute_audit_current_reality: ExecuteAuditCurrentReality,
        execute_design_story_implementation: ExecuteDesignStoryImplementation,
        execute_grade_story_design: ExecuteGradeStoryDesign,
        execute_draft_implementation_plan: Optional[ExecuteDraftImplementationPlan] = None,
        execute_publish_story_design_report: Optional[ExecutePublishStoryDesignReport] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        self._validate_source_document = validate_source_document or _valid_source_document
        self._validate_handoff = validate_handoff or _valid_handoff
        self._execute_audit_current_reality = execute_audit_current_reality
        self._execute_design_story_implementation = execute_design_story_implementation
        self._execute_grade_story_design = execute_grade_story_design
        self._execute_draft_implementation_plan = execute_draft_implementation_plan
        self._execute_publish_story_design_report = execute_publish_story_design_report
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

    async def _validate_artifact(self, output_path: str, schema_path: str) -> HandoffValidationResult:
        self._logger.info("Validating handoff artifact %s against schema %s", output_path, schema_path)
        result = await self._validate_handoff(output_path, schema_path)
        self._logger.info("Handoff validation result: valid=%s rule=%s", result.valid, result.rule.value)
        return result

    async def run(self, analysis_path: Optional[str]) -> WorkflowResult:
        self._logger.info("Starting story design for %s", analysis_path)
        self._logger.info("RequestSourceDocumentValidation validation_stage=startup")
        validation = await self._validate_source_document(analysis_path)
        if not validation.valid:
            self._logger.info("RejectSourceDocumentStartup validation_rule=%s", validation.rule.value)
            return WorkflowResult(
                design_path=None,
                passed=False,
                final_status="validation_failed",
                score=None,
                validation_rule=validation.rule,
            )

        design_path = None
        try:
            audit_path = await self._run_audit_current_reality(analysis_path)
            audit_handoff = await self._validate_artifact(audit_path, AUDIT_SCHEMA_PATH)
            if not audit_handoff.valid:
                return WorkflowResult(
                    design_path=None,
                    passed=False,
                    final_status="handoff_failed",
                    score=None,
                    handoff_rule=audit_handoff.rule,
                )

            design_path = await self._run_design_story_implementation(analysis_path, audit_path)
            design_handoff = await self._validate_artifact(design_path, DESIGN_SCHEMA_PATH)
            if not design_handoff.valid:
                return WorkflowResult(
                    design_path=design_path,
                    passed=False,
                    final_status="handoff_failed",
                    score=None,
                    handoff_rule=design_handoff.rule,
                )

            grade = await self._run_grade_story_design(design_path)

            if grade["passed"]:
                self._logger.info("Design grade passed; drafting implementation plan")
                if self._execute_draft_implementation_plan is not None:
                    plan = await self._execute_draft_implementation_plan(design_path)
                    plan_path = plan["output_path"]
                    plan_handoff = await self._validate_artifact(plan_path, PLAN_SCHEMA_PATH)
                    if not plan_handoff.valid:
                        return WorkflowResult(
                            design_path=design_path,
                            plan_path=None,
                            passed=False,
                            final_status="handoff_failed",
                            score=grade.get("score"),
                            handoff_rule=plan_handoff.rule,
                        )
                else:
                    plan_path = None
                self._logger.info("Implementation plan complete: %s", plan_path)
                if self._execute_publish_story_design_report is not None:
                    publish = await self._execute_publish_story_design_report(design_path, plan_path, grade.get("score"), analysis_path)
                    report_path = publish["output_path"]
                else:
                    report_path = None
                self._logger.info("Story design report complete: %s", report_path)
                return WorkflowResult(
                    design_path=design_path,
                    plan_path=plan_path,
                    report_path=report_path,
                    passed=True,
                    final_status="passed",
                    score=grade.get("score"),
                )
        except ActivityFailure:
            self._logger.error("Activity failed after exhausting retries")
            return WorkflowResult(
                design_path=design_path,
                passed=False,
                final_status="failed",
                score=None,
            )

        self._logger.info("Design grade did not pass; publishing failed report")
        if self._execute_publish_story_design_report is not None:
            publish = await self._execute_publish_story_design_report(design_path, None, grade.get("score"), analysis_path)
            report_path = publish["output_path"]
        else:
            report_path = None
        return WorkflowResult(
            design_path=design_path,
            plan_path=None,
            report_path=report_path,
            passed=False,
            final_status="failed",
            score=grade.get("score"),
        )
