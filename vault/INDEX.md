# Vault Index

This vault captures architectural decisions, patterns, and operational knowledge for the agentic software factory template.

## Decisions (ADRs)

- [ADR-001: Vault Protocol for Agentic Wiki](decisions/ADR-001-vault-protocol-agentic-wiki.md)
- [ADR-002: Software Factory Purpose & Dual Audience](decisions/ADR-002-software-factory-dual-audience.md)
- [ADR-003: Skills-Based Architecture with Workflow Coordination](decisions/ADR-003-skills-based-architecture.md)
- [ADR-004: Skill Output Contracts & Sentinel Files](decisions/ADR-004-skill-output-contracts.md)
- [ADR-005: Quantitative vs. Qualitative Analysis Separation](decisions/ADR-005-analysis-separation.md)
- [ADR-006: Grader Skill Pattern](decisions/ADR-006-grader-skill-pattern.md)
- [ADR-007: Skill Input Independence](decisions/ADR-007-skill-input-independence.md)
- [ADR-009: Colocate `story_analysis_workflow` config with its module](decisions/ADR-009-colocate-workflow-config.md)
- [ADR-010: Story Analysis WorkflowID Uses a Kickoff-Time Zettel ID, Not a Content Hash](decisions/ADR-010-workflow-id-zettel-timestamp.md)
- [ADR-011: Workflow-aware file logging for the Story Analysis Orchestrator](decisions/ADR-011-workflow-logging.md)
- [ADR-012: Skill Activity Invocation Configuration](decisions/ADR-012-skill-activity-invocation-configuration.md)
- [ADR-013: Three-Layer Workflow Module Architecture](decisions/ADR-013-three-layer-workflow-module-architecture.md)
- [ADR-014: Colocated Skill Activity Configuration and Template Method](decisions/ADR-014-colocated-skill-activity-template-method.md)
- [ADR-015: Devin Cost Metric Capture Scope](decisions/ADR-015-devin-cost-metric-scope.md)
- [ADR-016: Consolidated Story Analysis Run Reporting](decisions/ADR-016-consolidated-run-reporting.md)
- [ADR-017: Agentic EDD Quality Ratchet](decisions/ADR-017-agentic-edd-quality-ratchet.md)
- [ADR-018: Explicit Target Repository Context for Agentic Workflows](decisions/ADR-018-target-repository-context.md)
- [ADR-019: EDD Multi-Iteration Loop](decisions/ADR-019-edd-multi-iteration-loop.md)
- [ADR-020: Cadence Python SDK Serialization and Reconstruction Require JSON-Safe Types and Explicit Type Hints](decisions/ADR-020-cadence-python-sdk-serialization-and-types.md)
- [ADR-021: EDD Evaluation Commands May Exit Non-Zero and Inspect Commands Return Raw Result Lists](decisions/ADR-021-edd-evaluation-command-contracts.md)
- [ADR-022: Capture Raw EDD Evaluation Command Artifacts](decisions/ADR-022-edd-evaluation-command-artifacts.md)
- [ADR-023: Persistent, Process-Safe Mutation Lease for EDD](decisions/ADR-023-persistent-process-safe-mutation-lease.md)

 
## Services

- [Cadence local SQLite stack](services/cadence.md)
- [Devin ATIF usage exports](services/devin-atif.md)
- [EDD Refinement ProgressRecord](services/edd_refinement.md)
- [grade-story-design eval-suite refinement process](services/grade-story-design-eval-refinement.md)
- [NixOS development environment](services/nixos.md)
- [Secret protection for env files](services/secret-protection.md)
