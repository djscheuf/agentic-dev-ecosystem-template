# Windsurf Cascade Hooks

## Overview

Windsurf Cascade Hooks are automatically executed scripts triggered by specific events in the AI-assisted development workflow. They provide continuous, incremental verification and auditing as you interact with the Cascade AI assistant.

## What Are Hooks?

Hooks are event-driven scripts that run at key points during your Cascade conversation:

- **Before code is written** - Prevent accidental commits of secrets or sensitive data
- **After code edits** - Run fast verification checks (linting, type checking)
- **Before commands execute** - Gate dangerous operations like `git push` or `git merge`
- **After Cascade responses** - Capture conversation history for analysis and improvement

Unlike traditional Git hooks that run during Git operations, Cascade hooks integrate directly into the AI interaction stream, providing real-time feedback and safety gates.

## Core Concepts

### Event-Driven Execution

Hooks respond to specific events in the Cascade lifecycle:

1. **`pre_write_code`** - Triggered before Cascade writes any file changes
2. **`post_write_code`** - Triggered after Cascade completes file edits
3. **`pre_run_command`** - Triggered before Cascade executes terminal commands
4. **`post_cascade_response`** - Triggered after Cascade generates a response
5. **`post_cascade_response_with_transcript`** - Triggered after responses, includes full conversation transcript

### Incremental Verification

Rather than waiting until commit time to catch issues, hooks provide continuous feedback:

- **Fast feedback loops** - Catch issues immediately after edits
- **Progressive quality gates** - Different verification levels for different stages
- **Context-aware checks** - Only run relevant verifications based on changed files

### Conversation Auditing

The most powerful hook capability is capturing the conversation history between you and Cascade. This enables:

- **Retrospective analysis** - Review how features were implemented
- **Prompt evaluation** - Identify which prompts and workflows work best
- **Continuous improvement** - Refine rules and workflows based on real usage
- **Knowledge extraction** - Build institutional knowledge from successful patterns

## Hook Configuration

Hooks are configured in `.windsurf/hooks.json`:

```json
{
  "hooks": {
    "pre_write_code": [
      {
        "command": ".windsurf/scripts/verify-secrets.sh --scope=staged",
        "show_output": true
      }
    ],
    "post_write_code": [
      {
        "command": ".windsurf/scripts/post-edit-verify-windsurf.sh",
        "show_output": true
      }
    ],
    "pre_run_command": [
      {
        "command": ".windsurf/scripts/pre-tool-verify-windsurf.sh",
        "show_output": true
      }
    ],
    "post_cascade_response": [
      {
        "command": ".windsurf/scripts/post-cascade-verify-cycle.sh",
        "show_output": true
      }
    ],
    "post_cascade_response_with_transcript": [
      {
        "command": "node .windsurf/scripts/audit-logger.js",
        "show_output": true
      }
    ]
  }
}
```

## Available Hooks

### Secret Detection (`verify-secrets.sh`)

**Event:** `pre_write_code`  
**Purpose:** Prevent accidental commits of API keys, passwords, and other secrets

Scans files before they're written to detect common secret patterns:
- AWS access keys
- API tokens (OpenAI, GitHub, Slack)
- Database connection strings
- Private keys
- Bearer tokens

**Usage:**
```bash
.windsurf/scripts/verify-secrets.sh --scope=staged
.windsurf/scripts/verify-secrets.sh --scope=changed
.windsurf/scripts/verify-secrets.sh --scope=all
```

### Post-Edit Verification (`post-edit-verify-windsurf.sh`)

**Event:** `post_write_code`  
**Purpose:** Fast verification after code edits

Runs lightweight checks appropriate for the edited file type:
- TypeScript/JavaScript: ESLint
- .NET: Code formatting checks
- Automatically detects affected packages/projects

### Pre-Command Gate (`pre-tool-verify-windsurf.sh`)

**Event:** `pre_run_command`  
**Purpose:** Gate dangerous Git operations

Intercepts `git push` and `git merge` commands to run full verification before allowing them to proceed. Prevents pushing broken code.

### TDD Cycle Verification (`post-cascade-verify-cycle.sh`)

**Event:** `post_cascade_response`  
**Purpose:** Detect TDD cycle completion and verify before handoff

Monitors Cascade responses for TDD cycle completion signals and runs verification to ensure code quality before returning control to the developer.

### Conversation Audit Logger (`audit-logger.js`)

**Event:** `post_cascade_response_with_transcript`  
**Purpose:** Capture conversation history for analysis and improvement

The most valuable hook - captures every turn of your Cascade conversation into structured markdown files. See [Conversation Audit Hook](./conversation-audit-hook.md) for detailed documentation.

## Hook Input Format

Hooks receive JSON input via stdin containing event metadata:

```json
{
  "trajectory_id": "unique-conversation-id",
  "execution_id": "unique-turn-id",
  "timestamp": "2024-01-15T10:30:00Z",
  "tool_info": {
    "file_path": "/path/to/edited/file.ts",
    "command_line": "git push origin main",
    "transcript_path": "/tmp/cascade-transcript.jsonl"
  }
}
```

The `lib/common.sh` library provides helper functions to parse this input across different IDE formats (Windsurf, Claude, Cursor).

## Exit Codes

Hooks communicate results through exit codes:

- **0** - Success, allow operation to proceed
- **2** - Block operation (verification failed, dangerous command detected, etc.)
- **Other** - Error in hook execution

## Benefits

### Immediate Feedback

Catch issues within seconds of making changes, not minutes or hours later:
- Typos and syntax errors
- Type mismatches
- Linting violations
- Accidentally committed secrets

### Safety Gates

Prevent costly mistakes:
- Pushing broken code to remote
- Merging untested changes
- Committing sensitive credentials
- Deploying without verification

### Continuous Improvement

Build a feedback loop for your AI-assisted development:
- Analyze which prompts lead to successful implementations
- Identify patterns in failed attempts
- Refine rules and workflows based on real usage
- Create institutional knowledge from conversation history

### Context Preservation

Never lose track of how features were implemented:
- Full conversation history in readable markdown
- Searchable archive of implementation decisions
- Ability to replay successful patterns
- Documentation of problem-solving approaches

## Getting Started

1. **Review hook configuration** in `.windsurf/hooks.json`
2. **Customize verification scripts** for your project structure
3. **Test hooks manually** before relying on automatic execution
4. **Monitor hook output** during Cascade conversations
5. **Review audit logs** in `.audit/conversations/` to understand patterns

## Customization

### Adding New Hooks

1. Create a new script in `.windsurf/scripts/`
2. Make it executable: `chmod +x .windsurf/scripts/your-hook.sh`
3. Add entry to `.windsurf/hooks.json`
4. Test manually before enabling

### Modifying Existing Hooks

All hook scripts are in `.windsurf/scripts/` and can be customized:
- Adjust verification strictness
- Add project-specific checks
- Modify output formatting
- Change exit conditions

### Disabling Hooks

To temporarily disable a hook, comment it out in `hooks.json` or remove the entry entirely.

## Best Practices

1. **Keep hooks fast** - Slow hooks interrupt the development flow
2. **Provide clear output** - Developers need to understand why hooks block
3. **Use appropriate gates** - Not every hook should block operations
4. **Test hooks independently** - Ensure they work before enabling automatic execution
5. **Review audit logs regularly** - Extract value from conversation history

## Troubleshooting

### Hook Not Running

- Verify `.windsurf/hooks.json` is valid JSON
- Check that scripts are executable (`chmod +x`)
- Review Windsurf hook logs for errors

### Hook Blocking Incorrectly

- Run the hook script manually to debug
- Check exit codes and output
- Adjust verification criteria in the script

### Slow Hook Execution

- Profile which checks are slow
- Consider running expensive checks only on specific events
- Use parallel execution where possible

## Related Documentation

- [Conversation Audit Hook](./conversation-audit-hook.md) - Detailed guide to the audit logger
- [Creating Custom Hooks](./creating-custom-hooks.md) - Step-by-step guide for new hooks
- [Hook Library Reference](./hook-library-reference.md) - Documentation for `lib/common.sh` utilities

## Further Reading

- [Windsurf Hooks Documentation](https://docs.windsurf.ai/hooks) - Official Windsurf documentation
- [Git Hooks](https://git-scm.com/book/en/v2/Customizing-Git-Git-Hooks) - Traditional Git hooks for comparison
