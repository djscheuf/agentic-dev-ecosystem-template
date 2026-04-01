# Cascade Conversation Audit Logs

This directory contains automatically captured logs of Cascade conversations for analysis and improvement.

## Directory Structure

```
.audit/
├── turns/              # Raw JSONL transcripts per execution
│   └── {trajectory_id}_{execution_id}.jsonl
└── conversations/      # Human-readable markdown histories
    └── {trajectory_id}_{YYYYmmDDHHMM}.md
```

## File Naming Convention

### Turns (JSONL)
- **Format:** `{trajectory_id}_{execution_id}.jsonl`
- **Example:** `abc123def456_exec789.jsonl`
- **Content:** Raw structured data from Windsurf's transcript system

### Conversations (Markdown)
- **Format:** `{trajectory_id}_{YYYYmmDDHHMM}.md`
- **Example:** `abc123def456_202603110821.md`
- **Timestamp:** Date/time of the first turn in the conversation
- **Content:** Compiled markdown history showing user prompts and agent responses

## How It Works

The audit system uses Windsurf's `post_cascade_response_with_transcript` hook to automatically capture conversation data:

1. **Hook triggers** after each Cascade response
2. **Script runs** (`.windsurf/scripts/audit-logger.js`)
3. **Turn saved** to `turns/` as JSONL
4. **Markdown updated** in `conversations/` with new interactions

## Markdown Format

Each conversation file contains:
- **User** sections showing prompts
- **Agent** sections showing responses
- **Action** subsections showing:
  - Code edits
  - Commands executed
  - Files read
  - Searches performed
  - Tool usage

## Usage for Analysis

### Find patterns in user prompts
```bash
grep -r "## User" conversations/
```

### Analyze agent actions
```bash
grep -r "### Action:" conversations/
```

### Review specific conversation
```bash
cat conversations/{trajectory_id}_*.md
```

### Parse structured data
```bash
jq '.' turns/{trajectory_id}_*.jsonl
```

## Privacy & Security

⚠️ **Warning:** These files contain:
- Your prompts and questions
- Agent responses
- Code snippets from your codebase
- Command outputs
- File contents

**Recommendations:**
- Review `.gitignore` settings for your team's needs
- Consider encrypting if storing sensitive data
- Regularly clean up old logs if disk space is a concern

## Configuration

Hook configuration: `.windsurf/hooks.json`
Logger script: `.windsurf/scripts/audit-logger.js`

To disable audit logging, remove or comment out the hook in `.windsurf/hooks.json`.
