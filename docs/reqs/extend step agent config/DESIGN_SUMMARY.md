# Design Summary: Per-Step Agent Configuration

**Status:** Design Complete  
**Date:** 2026-05-06  
**Grade:** 8.8/10

## Overview

This document summarizes the design for extending the step architecture to support per-step agent configurations, enabling fine-grained permission control in non-interactive Devin CLI execution.

## Key Design Decisions

### 1. Config Strategy: Replace (Not Merge)
- **Decision:** Step-specific config completely replaces global config
- **Rationale:** Simpler, more predictable, better for least-privilege security
- **Impact:** Each step gets only the permissions it declares

### 2. Validation Responsibility: Wrapper Validates
- **Decision:** Check config file existence in saga validator; structure validation delegated to Devin CLI
- **Rationale:** Fail fast on missing files; delegate format validation for flexibility
- **Impact:** Clear error messages; no unnecessary coupling to Devin CLI internals

### 3. Path Resolution: Relative to Step Directory
- **Decision:** Paths resolve relative to step directory by default; absolute paths supported
- **Rationale:** Follows existing pattern for prompts and verify scripts; portable configs
- **Impact:** Configs can be co-located with steps; easy to move steps around

### 4. NodeDefinition: No Extension
- **Decision:** Keep agent_config in step.json only; don't add to NodeDefinition
- **Rationale:** Agent configuration is step-specific, not saga-level concern
- **Impact:** Simpler schema; less coupling; saga_models.py remains focused on graph structure

### 5. Backward Compatibility: Optional Field
- **Decision:** agent_config is optional; missing field triggers fallback to global config
- **Rationale:** All existing steps continue to work without modification
- **Impact:** Zero migration burden; can adopt gradually

## Architecture

### Layer Responsibilities

**Orchestration Layer (StepDefinition)**
- Load agent_config field from step.json
- Resolve path relative to step directory
- Store resolved path for use by wrapper

**Devin Wrapper Layer (DevinWrapper)**
- Receive agent_config path from StepDefinition
- Use step-specific config if available
- Fall back to global config if not specified
- Pass --agent-config flag to Devin CLI

**Validation Layer (Saga Validator)**
- Check agent_config file exists if specified
- Provide clear error messages for missing files
- Validate file is readable

### Data Model Changes

**StepDefinition Class**
```python
class StepDefinition:
    def __init__(self, data: dict, step_def_dir: Path):
        # ... existing fields ...
        self.agent_config = data.get("agent_config")  # NEW
    
    def get_agent_config_path(self) -> Optional[Path]:  # NEW
        """Resolve agent_config path relative to step directory."""
        if not self.agent_config:
            return None
        path = Path(self.agent_config)
        if not path.is_absolute():
            path = self.step_def_dir / path
        return path
```

**Step Definition JSON Schema**
```json
{
  "prompt": "...",
  "model": "...",
  "agent_config": "agent-config.json",  // NEW - optional
  "timeout": 60,
  "verify": "verify.sh"
}
```

## Implementation Phases

### Phase 1: Core Functionality
- Add agent_config field to StepDefinition
- Implement path resolution
- Update DevinWrapper to use step-specific config
- Fall back to global config if not specified

### Phase 2: Validation
- Add agent_config validation to saga validator
- Check file existence and readability
- Provide clear error messages

### Phase 3: Testing
- Unit tests for StepDefinition changes
- Unit tests for path resolution
- Integration tests for saga execution
- Backward compatibility verification

## User Workflow

### Before (Current Reality)
1. Create step.json with prompt, model, timeout, verify
2. All steps use global .devin/agent-config.json
3. Global config must grant broad permissions to accommodate all steps
4. Security risk: steps have more permissions than needed

### After (Target State)
1. Create step.json with optional agent_config field
2. Create step-specific agent-config.json with minimal permissions
3. Devin CLI executes with only needed permissions
4. Security benefit: principle of least privilege per step

## Risk Mitigation

| Risk | Mitigation | Verification |
|------|-----------|--------------|
| Backward compatibility breaks | agent_config is optional; fallback to global | Run existing tests; verify all steps work |
| Path resolution edge cases | Follow existing pattern; use pathlib | Unit tests for relative, absolute, edge cases |
| Devin CLI flag support | Verify --agent-config works in non-interactive mode | Manual testing with Devin CLI |
| Config validation errors unclear | Detailed error messages in saga validator | Test error messages; ensure they guide users |

## Testing Strategy

### Unit Tests
- StepDefinition with/without agent_config
- Path resolution (relative, absolute, edge cases)
- DevinWrapper command building
- Fallback to global config

### Integration Tests
- Saga execution with step-specific config
- Saga validation with missing/valid config files
- Backward compatibility with existing steps

### Test Fixtures
- Step with agent-config.json
- Step without agent-config.json
- Step with invalid config path
- Step with absolute config path

## Error Handling

### Missing Config File
```
ERROR: Step 'my-step' references agent_config 'agent-config.json' but file not found
Expected: steps/my-step/agent-config.json
```

### Missing Global Config (Fallback)
```
ERROR: Step 'my-step' has no agent_config and global config not found
Expected: .devin/agent-config.json
```

### Permission Denied
```
ERROR: Step 'my-step' agent_config file not readable
File: steps/my-step/agent-config.json
Check file permissions
```

## Acceptance Criteria Mapping

| Criterion | Design Element | Status |
|-----------|---|---|
| Optional agent_config field | StepDefinition.agent_config + get_agent_config_path() | ✓ |
| Fallback to global config | DevinWrapper.build_devin_command() conditional | ✓ |
| Pass to Devin CLI | --agent-config flag in command | ✓ |
| Relative path resolution | get_agent_config_path() implementation | ✓ |
| Validation | Saga validator file existence check | ✓ |
| Absolute paths supported | Path resolution logic | ✓ |

## Implementation Checklist

- [ ] Add agent_config field to StepDefinition
- [ ] Implement get_agent_config_path() method
- [ ] Update DevinWrapper.build_devin_command()
- [ ] Add validation to saga_validator.py
- [ ] Write unit tests for StepDefinition
- [ ] Write unit tests for DevinWrapper
- [ ] Write integration tests
- [ ] Verify backward compatibility
- [ ] Update documentation and examples

## Next Steps

1. **Resolve Remaining Questions** (if any)
2. **Create Implementation Plan** - Break into workstreams if needed
3. **Implement with TDD** - Write failing tests first
4. **Verify Backward Compatibility** - Run full test suite
5. **Update Documentation** - Add examples and schema

## Related Artifacts

- **Requirement:** `docs/reqs/extend-step-agent-config.md`
- **Analysis:** `extend-step-agent-config.analysis.json`
- **Analysis Grade:** `extend-step-agent-config.analysis-grade.json`
- **Audit:** `extend-step-agent-config.audit.json`
- **Design:** `extend-step-agent-config.design.json`
- **Design Grade:** `extend-step-agent-config.design-grade.json`

## Related ADRs

- [ADR-008: Devin CLI Saga Orchestration](../vault/decisions/ADR-008-devin-saga-orchestration.md)
- [ADR-009: Saga State Persistence](../vault/decisions/ADR-009-saga-state-persistence.md)
