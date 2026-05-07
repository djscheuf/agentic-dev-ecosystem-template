# Step-Specific Agent Configuration Guide

## Quick Start

Add per-step agent configuration to implement the principle of least privilege:

### 1. Create agent-config.json in your step directory
```json
{
  "permissions": {
    "allow": ["Read(src/**)", "Write(src/**)"],
    "deny": ["Write(.env*)", "Write(.git*)"]
  }
}
```

### 2. Reference it in step.json
```json
{
  "prompt": "Your prompt here",
  "model": "claude-opus-4.1",
  "agent_config": "agent-config.json"
}
```

### 3. Run your step
```bash
python orchestrator/devin_wrapper.py steps/my-step/step.json
```

That's it! Your step now runs with restricted permissions.

---

## Overview

Step-specific agent configuration allows each step to define its own Devin agent permissions. This improves security by implementing the principle of least privilege at the step level.

### Why Use Step-Specific Configs?

**Before (Global Config Only):**
- One config for all steps
- Must grant broad permissions to accommodate all steps
- Security risk: each step has access to everything

**After (Step-Specific Configs):**
- Each step declares only needed permissions
- Read-only steps can't write files
- Deployment steps can have broader access
- Better security and auditability

### Key Benefits

✅ **Security:** Each step has minimal necessary permissions  
✅ **Auditability:** Clear record of what each step can access  
✅ **Flexibility:** Different permission levels for different steps  
✅ **Backward Compatible:** Existing steps continue to work  

---

## How It Works

### Path Resolution

Paths in `agent_config` are resolved relative to the step directory:

```
steps/
  my-step/
    step.json                 # "agent_config": "agent-config.json"
    agent-config.json         # ← Resolved to this location
```

### Fallback Behavior

If a step doesn't specify `agent_config`, it falls back to the global config:

```
Global config: .devin/agent-config.json
```

This ensures backward compatibility with existing steps.

### Validation

During saga validation, the system checks:
- ✅ Config file exists
- ✅ File is readable
- ✅ JSON is valid
- ✅ Permissions structure is correct

---

## Permission Patterns

### Read-Only (Analysis Tasks)
```json
{
  "permissions": {
    "allow": ["Read(**)", "Read(docs/**)"],
    "deny": ["Write(**)", "Write(.env*)", "Write(.git*)"]
  }
}
```
**Use for:** Code reviews, audits, analysis

### Code Generation (Limited Write)
```json
{
  "permissions": {
    "allow": [
      "Read(src/**)",
      "Read(tests/**)",
      "Write(src/**)",
      "Write(tests/**)"
    ],
    "deny": [
      "Write(*.lock)",
      "Write(.env*)",
      "Write(.git*)"
    ]
  }
}
```
**Use for:** Code generation, refactoring, test writing

### Deployment (Broad Access)
```json
{
  "permissions": {
    "allow": ["Read(**)", "Write(**"]
    "deny": ["Write(.env*)", "Write(.git*)"]
  }
}
```
**Use for:** Deployment, infrastructure changes

### Documentation Only
```json
{
  "permissions": {
    "allow": [
      "Read(**)",
      "Write(docs/**)",
      "Write(*.md)"
    ],
    "deny": [
      "Write(.env*)",
      "Write(.git*)",
      "Write(src/**)"
    ]
  }
}
```
**Use for:** Documentation generation, README updates

---

## Common Patterns

### Shared Configs

Create shared configs for common permission patterns:

```
steps/
  shared/
    read-only-config.json
    code-gen-config.json
    deployment-config.json
  step-a/
    step.json              # "agent_config": "../shared/read-only-config.json"
  step-b/
    step.json              # "agent_config": "../shared/code-gen-config.json"
```

### Config Inheritance

Use a base config and extend it:

```
steps/
  shared/
    base-config.json       # Common deny patterns
  step-a/
    agent-config.json      # Extends base with specific allows
```

### Environment-Specific Configs

Different configs for different environments:

```
steps/
  deploy/
    agent-config.dev.json
    agent-config.prod.json
```

---

## Step-by-Step Examples

### Example 1: Code Review Step

**Goal:** Review code without modifying it

**step.json:**
```json
{
  "prompt": "Review the code and suggest improvements",
  "model": "claude-opus-4.1",
  "agent_config": "agent-config.json"
}
```

**agent-config.json:**
```json
{
  "permissions": {
    "allow": [
      "Read(src/**)",
      "Read(tests/**)",
      "Read(docs/**)"
    ],
    "deny": [
      "Write(**)",
      "Write(.env*)",
      "Write(.git*)"
    ]
  }
}
```

### Example 2: Code Generation Step

**Goal:** Generate code in src/ and tests/

**step.json:**
```json
{
  "prompt": "Generate unit tests for the provided code",
  "model": "claude-opus-4.1",
  "agent_config": "agent-config.json"
}
```

**agent-config.json:**
```json
{
  "permissions": {
    "allow": [
      "Read(src/**)",
      "Read(tests/**)",
      "Write(tests/**)"
    ],
    "deny": [
      "Write(src/**)",
      "Write(*.lock)",
      "Write(.env*)",
      "Write(.git*)"
    ]
  }
}
```

### Example 3: Deployment Step

**Goal:** Deploy application (broad access)

**step.json:**
```json
{
  "prompt": "Deploy the application to production",
  "model": "claude-opus-4.1",
  "agent_config": "agent-config.json"
}
```

**agent-config.json:**
```json
{
  "permissions": {
    "allow": [
      "Read(**)",
      "Write(**)"
    ],
    "deny": [
      "Write(.env*)",
      "Write(.git*)"
    ]
  }
}
```

---

## Migration Guide

### From Global Config Only

If you're currently using only `.devin/agent-config.json`:

**Step 1:** Create step-specific config
```bash
mkdir -p steps/my-step
cp .devin/agent-config.json steps/my-step/agent-config.json
# Edit to remove unnecessary permissions
```

**Step 2:** Update step.json
```json
{
  "prompt": "...",
  "model": "...",
  "agent_config": "agent-config.json"
}
```

**Step 3:** Test
```bash
python orchestrator/devin_wrapper.py steps/my-step/step.json
```

**Step 4:** Validate
```bash
python orchestrator/saga_executor.py sagas/my-saga.json --validate-only
```

---

## Best Practices

### 1. Principle of Least Privilege
Only grant permissions that the step actually needs:

```json
{
  "permissions": {
    "allow": [
      "Read(src/**)",
      "Write(src/**)"
    ],
    "deny": [
      "Write(.env*)",
      "Write(.git*)",
      "Write(node_modules/**)"
    ]
  }
}
```

### 2. Document Your Permissions
Add a README explaining why each permission is needed:

```markdown
# Permissions for code-generation step

## Allow
- Read(src/**) - Need to read existing code for context
- Write(src/**) - Need to write generated code

## Deny
- Write(.env*) - Protect environment variables
- Write(.git*) - Protect version control
```

### 3. Test with Restrictive Configs
Always test your step with the agent config:

```bash
python orchestrator/devin_wrapper.py steps/my-step/step.json
```

### 4. Use Shared Configs
Create shared configs for common permission patterns:

```
steps/
  shared/
    read-only-config.json
    code-gen-config.json
  step-a/
    step.json  # "agent_config": "../shared/read-only-config.json"
  step-b/
    step.json  # "agent_config": "../shared/code-gen-config.json"
```

### 5. Version Control Your Configs
Commit agent configs to version control:

```bash
git add steps/*/agent-config.json
git commit -m "Add step-specific agent configurations"
```

### 6. Review Regularly
Audit permissions quarterly:
- Remove unnecessary permissions
- Update documentation
- Test with current Devin CLI version

---

## Troubleshooting

### Config File Not Found
```
Error: agent_config 'agent-config.json' which does not exist
```

**Solution:** Ensure file exists in step directory:
```bash
ls -la steps/my-step/agent-config.json
```

### Permission Denied
```
Error: agent-config.json is not readable
```

**Solution:** Check file permissions:
```bash
chmod 644 steps/my-step/agent-config.json
```

### Invalid JSON
```
Error: Failed to validate agent_config: Invalid JSON
```

**Solution:** Validate JSON:
```bash
python -m json.tool steps/my-step/agent-config.json
```

### Agent Cannot Access Files
```
Error: Permission denied: src/main.py
```

**Solution:** Check permission patterns:
```json
{
  "permissions": {
    "allow": [
      "Read(src/**)",  // Make sure pattern matches your files
      "Write(src/**)"
    ]
  }
}
```

For more troubleshooting, see [Agent Configuration Troubleshooting Guide](agent-config-troubleshooting.md).

---

## Reference

### Schema
See [Step Definition Schema](step-definition-schema.md) for complete documentation.

### Example Step
See [Example Step with Agent Config](../steps/example-with-config/README.md) for a runnable example.

### Troubleshooting
See [Agent Configuration Troubleshooting Guide](agent-config-troubleshooting.md) for common issues and solutions.

---

## FAQ

**Q: What if I don't specify agent_config?**  
A: The step falls back to the global `.devin/agent-config.json`.

**Q: Can I use absolute paths?**  
A: Yes, absolute paths are supported: `"agent_config": "/etc/devin/config.json"`

**Q: Can I share configs across steps?**  
A: Yes, use relative traversal: `"agent_config": "../shared/agent-config.json"`

**Q: What if the global config doesn't exist?**  
A: If a step doesn't specify agent_config and the global config is missing, validation will fail with a clear error message.

**Q: Can I merge step-specific and global configs?**  
A: No, step-specific config completely replaces the global config.

**Q: How do I test if my config works?**  
A: Run the step with `python orchestrator/devin_wrapper.py steps/my-step/step.json`

**Q: Can I use environment variables in paths?**  
A: Not currently, but you can use relative paths and symlinks.

---

## See Also

- [Step Definition Schema](step-definition-schema.md)
- [Example Step with Agent Config](../steps/example-with-config/README.md)
- [Agent Configuration Troubleshooting Guide](agent-config-troubleshooting.md)
- [Devin CLI Documentation](https://devin.ai/docs)
