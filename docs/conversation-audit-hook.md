# Conversation Audit Hook

## Overview

The Conversation Audit Hook is the most powerful component of the Windsurf Cascade Hooks system. It captures every turn of your conversation with the Cascade AI assistant, creating a searchable archive of implementation decisions, problem-solving approaches, and successful patterns.

## Purpose

The audit hook serves three critical functions:

1. **Retrospective Analysis** - Review how features were implemented to understand what worked and what didn't
2. **Prompt Evaluation** - Identify which prompts, rules, and workflows lead to successful outcomes
3. **Continuous Improvement** - Build a feedback loop to refine your AI-assisted development practices over time

## How It Works

### Event Trigger

The audit hook runs on the `post_cascade_response_with_transcript` event, which fires after every Cascade response and provides access to the full conversation transcript.

### Data Capture

For each conversation turn, the hook captures:

- **User input** - Your questions, requests, and clarifications
- **Applied rules** - Which rules were active during the turn
- **Agent responses** - Cascade's analysis and explanations
- **Code actions** - File edits with explanations and content
- **Command actions** - Terminal commands executed and their output
- **Tool usage** - Search queries, file reads, and other tool invocations

### Storage Format

The hook maintains two types of artifacts:

1. **Turn JSONL files** (`.audit/turns/`) - Raw JSON Lines format for programmatic analysis
2. **Conversation markdown files** (`.audit/conversations/`) - Human-readable conversation history

## File Structure

```
.audit/
├── logs/
│   └── audit-logger.log          # Hook execution logs with rotation
├── turns/
│   ├── conv-123_turn-001.jsonl   # Raw turn data
│   ├── conv-123_turn-002.jsonl
│   └── conv-123_turn-003.jsonl
└── conversations/
    └── conv-123.md                # Aggregated conversation history
```

## Conversation Markdown Format

Each conversation file contains:

### Header
```markdown
# Conversation: conv-123

**Started:** 2024-01-15T10:30:00Z

---
```

### Turn Structure
```markdown
## User

[Your request or question]

*Rules applied: active-partner, design-buddy*

## Agent

[Cascade's response and analysis]

### Action: Code Edit

**File:** `src/components/Button.tsx`

**Explanation:** Added onClick handler prop

<details>
<summary>New content</summary>

```
[Full file content]
```
</details>

### Action: Command

```bash
npm test -- Button.test.tsx
```

<details>
<summary>Output</summary>

```
[Command output]
```
</details>

---
```

## Use Cases

### 1. Retrospective Analysis

After implementing a feature, review the conversation to understand:

- **Decision points** - Why certain approaches were chosen
- **Problem-solving patterns** - How obstacles were overcome
- **Iteration cycles** - How the solution evolved through feedback
- **Time investment** - How many turns were needed for completion

**Example:**
```bash
# Find all conversations about authentication
grep -r "authentication" .audit/conversations/

# Review a specific implementation
cat .audit/conversations/conv-20240115-auth-implementation.md
```

### 2. Prompt Evaluation

Analyze which prompts lead to successful outcomes:

- **Effective workflows** - Which workflow sequences work best
- **Rule effectiveness** - Which rules improve code quality
- **Clarification patterns** - When Active Partner questioning helps vs. hinders
- **Instruction clarity** - Which phrasing leads to correct implementations

**Example:**
```bash
# Find conversations where TDD workflow was used
grep -r "tdd-workflow" .audit/conversations/

# Compare successful vs. failed implementations
# Review turns where Cascade asked clarifying questions
grep -A 10 "## User" .audit/conversations/conv-*.md | grep -B 5 "?"
```

### 3. Continuous Improvement

Build a feedback loop to refine your development practices:

- **Identify gaps in rules** - Find recurring issues that need new rules
- **Optimize workflows** - Streamline processes based on actual usage
- **Extract patterns** - Discover successful approaches to codify
- **Train team members** - Share effective interaction patterns

**Example workflow:**

1. **Weekly review** - Scan conversation logs for patterns
2. **Identify issues** - Note where Cascade struggled or misunderstood
3. **Create rules** - Write new rules to address common issues
4. **Update workflows** - Refine workflows based on what worked
5. **Measure improvement** - Compare new conversations to baseline

### 4. Knowledge Extraction

Transform conversation history into institutional knowledge:

- **Architecture decisions** - Document why systems are designed certain ways
- **Implementation patterns** - Extract reusable code patterns
- **Problem solutions** - Build a searchable database of solved problems
- **Best practices** - Identify and codify successful approaches

**Example:**
```bash
# Extract all architecture discussions
grep -r "architecture\|design decision\|ADR" .audit/conversations/ > architecture-decisions.md

# Find all test implementation patterns
grep -A 20 "test.*implementation" .audit/conversations/ > test-patterns.md
```

## Advanced Analysis

### Programmatic Analysis with JSONL

The raw JSONL files enable sophisticated analysis:

```javascript
// Count tool usage frequency
const fs = require('fs');
const turns = fs.readFileSync('.audit/turns/conv-123_turn-001.jsonl', 'utf-8')
  .split('\n')
  .filter(line => line.trim())
  .map(line => JSON.parse(line));

const toolUsage = {};
turns.forEach(step => {
  if (step.type === 'tool_use') {
    const tool = step.tool_use.tool_name;
    toolUsage[tool] = (toolUsage[tool] || 0) + 1;
  }
});

console.log('Tool usage:', toolUsage);
```

### Metrics to Track

- **Turns per feature** - Measure implementation efficiency
- **Rule application frequency** - Identify most valuable rules
- **Error patterns** - Find common mistakes to prevent
- **Workflow effectiveness** - Compare outcomes across workflows
- **Clarification rate** - Track how often Active Partner questioning occurs

## Building a Prompt Evaluation System

The audit logs provide the foundation for systematic prompt improvement:

### Phase 1: Baseline Collection

1. Use current rules and workflows for 2-4 weeks
2. Capture all conversations in audit logs
3. Tag conversations by outcome (success/partial/failure)

### Phase 2: Pattern Analysis

1. Review successful implementations
   - Which rules were applied?
   - Which workflows were used?
   - What was the turn count?
   - Were there clarification rounds?

2. Review failed implementations
   - Where did Cascade misunderstand?
   - Which rules were missing?
   - What additional context was needed?

### Phase 3: Hypothesis Formation

Based on patterns, form hypotheses:
- "Adding rule X will reduce clarification rounds"
- "Workflow Y works better for feature type Z"
- "Providing context A upfront eliminates issue B"

### Phase 4: Experimentation

1. Implement one change at a time
2. Continue capturing conversations
3. Compare metrics before/after
4. Validate or reject hypothesis

### Phase 5: Iteration

Repeat the cycle:
- Successful changes become permanent
- Failed experiments are reverted
- New patterns emerge for next cycle

## Real-World Example

### Before Audit Hook

Developer implements authentication feature:
- Takes 45 minutes
- Multiple back-and-forth clarifications
- Some security issues found in review
- No record of why certain decisions were made

### After Audit Hook

Same developer implements authorization feature:

1. **During implementation** - Conversation captured automatically
2. **After completion** - Reviews conversation markdown
3. **Identifies pattern** - Cascade struggled with security requirements
4. **Creates rule** - Adds `security-buddy.md` rule for future features
5. **Next feature** - Authorization v2 takes 20 minutes, no security issues
6. **Documentation** - Conversation serves as implementation guide for team

### Measurable Improvements

- **50% reduction** in implementation time
- **Zero security issues** in review
- **Reusable knowledge** for team members
- **Clear audit trail** for compliance

## Configuration

The audit hook is configured in `.windsurf/hooks.json`:

```json
{
  "hooks": {
    "post_cascade_response_with_transcript": [
      {
        "command": "node .windsurf/scripts/audit-logger.js",
        "show_output": true
      }
    ]
  }
}
```

### Customization Options

Modify `audit-logger.js` to:

- **Change storage location** - Update `.audit` path
- **Adjust log rotation** - Modify `MAX_LOG_SIZE_MB` and `MAX_LOG_FILES`
- **Filter content** - Skip certain conversation types
- **Add metadata** - Include timestamps, user info, project context
- **Export formats** - Generate HTML, PDF, or other formats

## Log Management

### Rotation

The audit logger automatically rotates its execution logs:
- Maximum log size: 5MB
- Maximum log files: 3
- Oldest logs are deleted automatically

### Cleanup

Conversation and turn files are never automatically deleted. Manage them manually:

```bash
# Archive old conversations
tar -czf conversations-2024-01.tar.gz .audit/conversations/conv-202401*.md
rm .audit/conversations/conv-202401*.md

# Clean up turn JSONL files older than 90 days
find .audit/turns -name "*.jsonl" -mtime +90 -delete
```

### Privacy Considerations

Audit logs may contain:
- Proprietary code
- Business logic
- API keys (if secret detection failed)
- Personal information

**Best practices:**
- Add `.audit/` to `.gitignore`
- Encrypt archived conversations
- Review logs before sharing
- Implement retention policies

## Troubleshooting

### Hook Not Running

Check execution logs:
```bash
cat .audit/logs/audit-logger.log
```

Common issues:
- Node.js not installed
- Invalid JSON in transcript
- Permission issues creating `.audit/` directory

### Missing Conversations

Verify hook configuration:
```bash
cat .windsurf/hooks.json | jq '.hooks.post_cascade_response_with_transcript'
```

Check that:
- Hook command path is correct
- Script is executable
- `show_output` is true for debugging

### Large File Sizes

Conversation files can grow large with code content. Options:

1. **Collapse code blocks** - Already using `<details>` tags
2. **Limit content length** - Modify `audit-logger.js` to truncate
3. **Separate storage** - Move code content to separate files
4. **Archive regularly** - Compress old conversations

## Future Enhancements

Potential improvements to the audit system:

- **Web UI** - Browse conversations in a web interface
- **Search indexing** - Full-text search across all conversations
- **Analytics dashboard** - Visualize metrics and trends
- **AI analysis** - Use AI to analyze conversation patterns
- **Integration** - Export to project management tools
- **Collaboration** - Share conversations with team members

## Related Documentation

- [Hooks Overview](./hooks-overview.md) - General hooks documentation
- [Creating Custom Hooks](./creating-custom-hooks.md) - Build your own hooks
- [Prompt Engineering Guide](./prompt-engineering.md) - Improve prompts using audit data

## Conclusion

The Conversation Audit Hook transforms ephemeral AI conversations into a valuable knowledge base. By systematically capturing, analyzing, and learning from your interactions with Cascade, you can:

- **Accelerate development** - Learn what works and replicate it
- **Improve quality** - Identify and prevent recurring issues
- **Build expertise** - Create institutional knowledge from experience
- **Optimize AI usage** - Refine prompts and workflows based on data

This is not just logging - it's building a continuous improvement system for AI-assisted development.
