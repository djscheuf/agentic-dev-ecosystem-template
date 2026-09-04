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

 
## Services

- [Cadence local SQLite stack](services/cadence.md)
- [NixOS development environment](services/nixos.md)
- [Orchestrator Harness (DevinHarness) — where it runs, auth gotchas](services/orchestrator-harness.md)
