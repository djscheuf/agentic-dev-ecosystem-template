# Requirement: Extend Step Architecture for Per-Step Agent Configuration

**Status:** Analyzed  
**Date:** 2026-05-06  
**Priority:** Medium  
**Complexity:** Low-Medium

## Overview

Extend the step architecture to allow each step to define its own Devin agent configuration, enabling fine-grained permission control in non-interactive mode. This improves security by implementing the principle of least privilege at the step level.

## Motivation

The Devin CLI enforces strong permission controls in non-interactive mode. Currently, all steps use a global `.devin/agent-config.json` that must grant broad permissions to accommodate all steps. By allowing per-step configurations, each step can declare only the permissions it actually needs, improving security and auditability.

## User Story

**As a** Step Developer  
**I want** Each step to implement its own agent-config that specifies permissions required for that step's actions  
**So that** The Devin agent can run with minimal necessary permissions in non-interactive mode, improving security and control

## Acceptance Criteria

1. **Step definition can include optional 'agent_config' field**
   - A step.json can specify `"agent_config": "agent-config.json"`
   - The path is resolved relative to the step directory
   - DevinWrapper uses the specified config when executing the step

2. **Backward compatibility with existing steps**
   - Steps without an agent_config field fall back to global `.devin/agent-config.json`
   - Existing steps continue to work without modification

3. **DevinWrapper passes step-specific config to Devin CLI**
   - When building the Devin command, include `--agent-config <path>` with the step-specific config
   - The path is correctly resolved before passing to CLI

4. **Configuration validation**
   - If agent_config is specified, the file must exist
   - Saga validation should catch missing config files with clear error messages
   - Invalid config structure should be rejected

5. **Path resolution**
   - Relative paths are resolved relative to the step directory
   - Absolute paths are supported
   - Path traversal (../) is handled safely

## Technical Scope

### Affected Components

- **orchestrator/devin_wrapper.py**
  - `StepDefinition` class: Add optional `agent_config` field
  - `DevinWrapper` class: Load and use step-specific config in `build_devin_command()`

- **orchestrator/saga_executor.py**
  - `_execute_step()` method: Pass step-specific config to DevinWrapper

- **orchestrator/saga_models.py**
  - Consider if `NodeDefinition` needs agent_config field

- **steps/*/step.json**
  - Schema extension to support optional `agent_config` field

- **Saga validation**
  - Validate that referenced agent_config files exist

### Implementation Approach

1. Add `agent_config` field to `StepDefinition` class
2. Implement path resolution logic (relative to step directory)
3. Update `DevinWrapper.build_devin_command()` to use step-specific config
4. Add validation in saga executor to check config file existence
5. Maintain backward compatibility by falling back to global config
6. Update step.json schema documentation

## Edge Cases

| Case | Impact | Handling |
|------|--------|----------|
| Empty/null agent_config | Should fall back to global config | Treat as not specified |
| Missing config file | Step execution fails | Validation error with clear message |
| Path traversal (../) | Security concern | Resolve safely relative to step dir |
| Missing global config | Fallback fails | Error indicates missing config |
| Permission denied on config | File not readable | Error indicates permission issue |
| Absolute paths | Flexibility | Support absolute paths in addition to relative |

## Open Design Questions

1. **Config merging strategy**: Should step-specific config completely replace the global config, or should they be merged? If merged, what's the merge strategy?

2. **Validation responsibility**: Should the wrapper validate config structure, or just pass it to Devin CLI? Early validation gives better errors; delegating gives flexibility.

3. **Environment variables**: Should config paths support environment variable expansion (e.g., `${STEP_DIR}/agent-config.json`)?

4. **Backward compatibility timeline**: When can we require agent_config? Should it be optional forever?

## Testing Strategy

- **Unit tests**: StepDefinition loading with/without agent_config
- **Unit tests**: Path resolution (relative, absolute, traversal)
- **Unit tests**: DevinWrapper command building with step-specific config
- **Integration tests**: Saga execution with step-specific configs
- **Validation tests**: Missing file, invalid structure, permission errors

## Documentation Updates

- Update step.json schema documentation
- Add example step with agent-config
- Document permission model and common patterns
- Add troubleshooting guide for config issues

## Related Decisions

- [ADR-008: Devin CLI Saga Orchestration](../vault/decisions/ADR-008-devin-saga-orchestration.md)
- [ADR-009: Saga State Persistence with File-Based Storage](../vault/decisions/ADR-009-saga-state-persistence.md)

## Analysis Artifacts

- Intent: `extend-step-agent-config.intent.json`
- Analysis: `extend-step-agent-config.analysis.json`
- Grade: `extend-step-agent-config.analysis-grade.json`
