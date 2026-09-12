---
name: pr-summary
description: Generate PR description and squash merge commit message
disable-model-invocation: true
---

# PR Summary Workflow

Use this workflow when preparing to merge a feature branch via Pull Request.

## Step 1: Gather Branch and Version Information

Check the current branch, version, and commit history:
```bash
git branch --show-current
cat package.json | grep '"version"'
git log --oneline --no-merges origin/main..HEAD
```

**Note**: Target branch defaults to `main` unless specified otherwise. Version is automatically read from `package.json`.

## Step 2: Identify Key Components

Review what was implemented by examining:
- API endpoints added/modified
- Business rules enforced
- Test coverage (run tests to get count)
- Infrastructure changes (Docker, database, etc.)
- Documentation created

## Step 3: Generate Squash Merge Commit Message

**Format**: Single-line summary + blank line + body (max 500 characters total)

**Template**:
```
<type>: <brief description> (v<version>)

<2-3 sentence overview>

Endpoints: <list endpoints>
Auth: <auth mechanism>
Rules: <key business rules>
Testing: <test count and methodology>
Infrastructure: <key infrastructure components>
Observability: <logging/monitoring features>
```

**Requirements**:
- ✅ Max 500 characters (excluding file stats)
- ✅ No file statistics (Git handles this)
- ✅ Focus on WHAT and WHY, not HOW
- ✅ Include version number if applicable

**Types**: feat, fix, refactor, docs, test, chore, perf, ci

## Step 4: Generate PR Description

**Format**: Markdown with sections

**Emoji Selection**:
- 📚 Use book emoji for documentation, workflow, or infrastructure changes
- 🎯 Use target emoji for feature implementation with code changes
- 🐛 Use bug emoji for bug fixes

**Template**:
```markdown
# <emoji> <Feature Name> (v<version>)

## Overview
<1-2 sentence summary>


## API Endpoints (if applicable)
- `METHOD /path` - Description

## Key Features
- **Category**: Details
- **Category**: Details

## Testing (<count> tests - <status>)
- **Component**: <count> tests (<focus areas>)

## Local Development (if applicable)
```bash
# Quick start commands
```

## Infrastructure (if applicable)
- Key infrastructure components

## Documentation
- List of docs created/updated (use relative paths from repo root, e.g., `docs/reqs/folder/file.md`)

## Stats
- **Tests**: <count> passing (<methodology>)
```

**Requirements**:
- ✅ 50% shorter than comprehensive version
- ✅ No file statistics
- ✅ Focus on user-facing features and testing
- ✅ Include quick-start commands if applicable
- ✅ Link to detailed docs for more info

## Step 5: Review Checklist

Before submitting PR:
- [ ] Commit message under 500 characters
- [ ] PR description is concise but complete
- [ ] All tests passing (include count)
- [ ] Version number included (if applicable)
- [ ] No file statistics in either summary
- [ ] Documentation links included
- [ ] Quick-start commands tested

## Step 6: Ask Clarifying Questions (Optional)

Before generating summaries, confirm if needed:
1. **Target branch**: Defaults to `main` (specify only if different)
2. **Version**: Automatically read from `package.json` (no need to ask)
3. **Breaking changes**: Any breaking changes to note?
4. **Special context**: Jira ticket, GitHub issue, or story ID to reference?

## Examples

### Good Commit Message (487 chars)
```
feat: implement View and Edit Tactics REST API (v1.0)

Complete REST API for viewing/editing marketing tactics with Clean Architecture and CQRS.

Endpoints: GET /api/tactics, GET /api/tactics/{id}, PATCH /api/tactics/{id}
Auth: Azure AD B2C role-based access (InternalRequester)
Rules: DRAFT-only edits, owner/requester access, date validation
Testing: 35 tests (100% passing), TDD methodology
Infrastructure: Docker + SQL Server 2022, auto-init, seeded data
Observability: Correlation IDs, structured logging
```

### Bad Commit Message (too verbose)
```
feat: implement complete REST API for viewing and editing marketing tactics

This PR implements a comprehensive REST API that allows users to view and edit
marketing tactics. It includes three endpoints, full authentication, business
rule validation, comprehensive testing, Docker setup, and more...
[continues for 800+ characters]
```

## Tips

1. **Be concise**: Every word should add value
2. **Use abbreviations**: "auth" not "authentication", "DB" not "database"
3. **Group related items**: Combine similar features into one line
4. **Prioritize**: Lead with most important features
5. **Test count matters**: Always include test count and status
6. **Version everything**: Include version numbers for releases