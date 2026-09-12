---
name: update-ramp-up-dossier
description: Generate or update the repository ramp-up dossier for onboarding new developers. Manual trigger only.
disable-model-invocation: true
---

# Update Ramp-Up Dossier Workflow

**Purpose**: Generate or refresh `docs/RAMP_UP_DOSSIER.md` — a single onboarding document that captures repo-specific terminology, patterns, architectural decisions, and recent development activity.

**When to run**: Only when explicitly requested by the user. This skill is **manual-trigger only** and should not be invoked automatically by the agent.

**Output**: `docs/RAMP_UP_DOSSIER.md`

**Scope**: Document only what is discoverable from the repository itself. Do not speculate about adjacent teams, the broader organization, or industry context beyond what is explicitly recorded in the repo.

---

## Step 1: Discover Repository Structure

Before reading content, map what the repo actually contains. Use the broadest applicable command for the platform (`ls -la`, `tree -L 2`, `find . -maxdepth 2 -type d`, etc.).

Identify the following categories:

**Documentation roots:**
- `README.md`
- `AGENTS.md` (if present — includes vault and agent conventions)
- `docs/` and its subdirectories
- `vault/` (per the Vault Protocol in `AGENTS.md`)
- `.devin/rules/`
- `.devin/skills/`

**Source roots:**
- `src/`, `apps/`, `packages/`, `lib/`, `modules/`, or equivalent
- Top-level language directories (`py/`, `go/`, `cs/`, etc.)

**Configuration:**
- `package.json`, `requirements.txt`, `pyproject.toml`, `Cargo.toml`, `go.mod`, etc.
- Workspace files (`pnpm-workspace.yaml`, `nx.json`, `turborepo.json`, etc.)
- `tsconfig.json`, `vite.config.*`, `webpack.config.*`, etc.
- `docker-compose.yml`, `Dockerfile`, `shell.nix`, `flake.nix`
- CI/CD files (`azure-pipelines.yml`, `.github/workflows/`, `.gitlab-ci.yml`, etc.)
- `.editorconfig`, `.eslintrc*`, `.prettierrc*`, `pyproject.toml` for lint/format

**Tests:**
- `tests/`, `test/`, `**/*.test.*`, `**/*.spec.*`, `e2e/`, `cypress/`, `playwright/`

Record the discovered layout in your working notes. Do not assume the presence of any specific file or directory.

---

## Step 2: Review Git History

Use git to understand the repo’s evolution, current activity, and team conventions.

Commands to run:
```bash
git log --oneline -30
git branch -a
git log --all --graph --oneline -20
git log --stat --since='3 months ago' --oneline -20
git log --grep='ADR\|decision\|migrat' --oneline -20
git shortlog -sne -10
```

Capture:
- Recent themes (what parts of the codebase are changing now)
- Active feature branches and their names
- Major migrations, refactors, or reorganizations
- Commit-message style (conventional, free-form, ticket-prefixed)
- Dominant contributors (for orientation, not PII)

Use these insights to frame the *Historical Context* and *Current Focus* sections.

---

## Step 3: Read the Foundational Documents

Read only what actually exists:

- `README.md` — project purpose, setup, prerequisites
- `AGENTS.md` — agent and vault conventions (if present)
- `vault/INDEX.md` — map of decisions, services, incidents, personas
- `docs/` — requirements, EDDs, process maps, API contracts
- `.devin/rules/` — active development rules
- `.devin/skills/` — available skills (read `SKILL.md` intros, not every detail)
- Root package/config files — stack and scripts

Do not invent setup steps or decisions. If a document is missing, skip it and note the gap.

---

## Step 4: Extract Domain, Patterns, and Stack

From the discovered sources, extract:

**Domain terminology:**
- Business concepts, entity names, acronyms
- Field and type names from `**/models/`, `**/types/`, or generated schemas
- Contract terms from API docs or generated OpenAPI specs

**Technical patterns and key players:**
- Architectural patterns found in source and ADRs (e.g., layered, clean, hexagonal, event-driven)
- Key components, services, utilities, or modules with their file paths
- State-management, validation, and testing patterns
- Monorepo or package structure, if any

**Historical context and architectural decisions:**
- ADRs in `vault/decisions/` or `docs/adrs/`
- Migration notes, deprecation warnings, major refactors from git history
- Trade-offs and alternatives mentioned in docs

**Technology stack:**
- Languages and runtimes
- Frameworks and libraries
- Build, test, and lint tools
- CI/CD and deployment tools
- Data stores and message brokers

---

## Step 5: Populate the Dossier Template

Create or overwrite `docs/RAMP_UP_DOSSIER.md` with this structure:

```markdown
# Ramp-Up Dossier: [Project Name]

**Last Updated**: [YYYY-MM-DD]

---

## Project Purpose
[What the codebase does, in one or two paragraphs, from README and `git log` themes.]

---

## Domain Terminology
[Project-specific terms, acronyms, and concepts discovered from code, contracts, and docs.]

- **Term**: Definition and source (e.g., `src/models/...` or `docs/reqs/...`).

---

## Repository Structure
[Top-level map of the repo with a short purpose for each major directory.]

```
root/
├── src/            [What it contains]
├── tests/          [What it contains]
├── docs/           [What it contains]
├── vault/          [Architectural decisions and operational knowledge]
├── .devin/         [Skills and rules for agentic workflows]
└── ...
```

---

## Technology Stack
[Languages, frameworks, libraries, build and test tools, CI/CD, containers.]

- **Language/Runtime**: ...
- **Web/Framework**: ...
- **Testing**: ...
- **Build/Package**: ...
- **CI/CD**: ...
- **Data/Storage**: ...

---

## Technical Patterns and Key Players
[Architectural patterns, recurring components, and important utilities.]

- **Pattern Name**: Description, why it is used, and where to find it (path or ADR).

---

## Historical Context and Architectural Decisions
[Major decisions, migrations, and trade-offs.]

- **Decision (Date)**: Summary, rationale, and link to ADR or commit range.

---

## Recent Development Focus
[What the team has been working on lately, from `git log --since='3 months ago'`.]

---

## Quick Start Guide

### Prerequisites
[From README and config files. Do not invent steps.]

### Local Setup
[Commands to build and run.]

### Running Tests
[Commands from package scripts or test config.]

### Common Workflows
[Link to `.devin/skills/`, `.windsurf/workflows/`, `docs/`, or similar.]

---

## Key Resources

**Architecture and Decisions:**
- [Link to `vault/decisions/` or `docs/adrs/`]
- [Link to relevant diagrams]

**Development Guidelines:**
- [Link to `AGENTS.md` or `.devin/rules/`]
- [Link to testing or coding guidelines]
- [Link to skill definitions]

**API and Requirements:**
- [Link to `docs/reqs/` or `docs/apis/`]
- [Link to generated schemas or contracts]
```

---

## Step 6: Verify and Write the File

**Accuracy checks:**
- [ ] All file paths and links point to existing files.
- [ ] ADR references match actual filenames in `vault/decisions/` or `docs/adrs/`.
- [ ] Technology versions match `package.json` or equivalent config.
- [ ] Setup and test commands are copied verbatim from docs/config, not invented.
- [ ] Last Updated date is today.

**Scope checks:**
- [ ] No speculation about external teams, organizational structure, or industry context.
- [ ] Every claim is tied to a specific file, ADR, or commit.
- [ ] Missing sections are marked `[Not found in repo]` rather than fabricated.

Write the final file to `docs/RAMP_UP_DOSSIER.md` and confirm the path.
