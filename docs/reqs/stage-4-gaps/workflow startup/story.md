# Validate Story Analysis Workflow Startup

## Story

So that invalid workflow requests fail before any agent work or incomplete evidence is produced
As a Story Analysis Workflow operator
I want the workflow to validate its source document at startup

## Entry Outcome

A workflow request is accepted for extraction only when `story_document` identifies an accessible Markdown file.

## Scope

### In Scope

- Run a distinct startup guardrail before `extract_story_intent`.
- Require `story_document` to be present and non-empty.
- Require the path to identify an existing, readable regular file.
- Require a Markdown file extension.
- Fail before scheduling the first Skill Activity when validation fails.
- Record a sanitized validation result that identifies the failed startup rule.
- Preserve current behavior for valid Markdown requests.

### Out of Scope

- Validating artifacts produced after workflow startup.
- Between-step file existence or schema checks.
- Ambiguity punch-out or human decision handling.
- Adversarial content review.
- Consolidated run reporting or success-rate aggregation.
- Per-agent Stage 3 quality remediation or certification evidence.

## Acceptance Criteria

- Given an existing readable Markdown file, when the workflow starts, then startup validation passes and `extract_story_intent` is scheduled exactly once.
- Given `story_document` is null, empty, or whitespace-only, when the workflow starts, then it fails startup validation and schedules no Skill Activity.
- Given `story_document` does not exist, identifies a directory, or is not readable, when the workflow starts, then it fails startup validation and schedules no Skill Activity.
- Given `story_document` has a non-Markdown extension, when the workflow starts, then it fails startup validation and schedules no Skill Activity.
- Given a valid Markdown path contains spaces or Unicode characters, when the workflow starts, then the path is validated without lossy normalization and extraction is scheduled.
- Given startup validation fails, when the workflow reaches its terminal state, then its observable result or workflow log identifies startup validation as the failure origin without exposing sensitive filesystem details.
- Automated tests cover valid input and every rejected input category without invoking the Devin harness for rejected requests.

## Dependencies

- Existing `StoryAnalysisWorkflow` startup and activity scheduling behavior.
- Existing workflow logging and terminal-result mechanisms.
- An agreed definition of supported Markdown extensions and readable-path behavior in the deployment environment.

## Exit Outcome

Startup behavior is deterministic and test evidence proves that no agent invocation occurs for an invalid source document.
