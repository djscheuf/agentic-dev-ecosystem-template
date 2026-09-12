# Cascade

Cascade is the legacy agent in Devin Desktop. New tabs default to Devin Local when available, but Cascade remains useful for existing workflows, memories, and MCP setups that have not been migrated.

## Migration

To migrate Cascade workflows and memories to Devin Local, run **Devin: Open Cascade Migration Wizard** from the Command Palette.

## Memories

Memories are auto-generated context snippets created during Cascade conversations.

- Stored locally in `~/.codeium/windsurf/memories/`.
- Associated with the workspace where they were created.
- Not committed to the repository.
- Do not consume credits to create or use.

For durable, shareable knowledge, prefer Rules, `AGENTS.md`, or skills.

## Rules

Rules tell Cascade how to behave. They can be defined at multiple scopes:

| Scope | Location | Notes |
|-------|----------|-------|
| Global | `~/.codeium/windsurf/memories/global_rules.md` | Always on. 6,000 character limit. |
| Workspace | `.devin/rules/*.md` (preferred) or `.windsurf/rules/*.md` | One file per rule. 12,000 character limit each. `.windsurfrules` at workspace root also supported. |
| AGENTS.md | Any directory in the workspace | Root = always-on; subdirectory = glob-scoped. |
| System (Enterprise) | `/etc/devin/rules/` or `/etc/windsurf/rules/` | IT-managed, read-only. |

### Activation modes

Rules use frontmatter `trigger` values:

| `trigger` | Behavior | Context cost |
|-----------|----------|--------------|
| `always_on` | Included in the system prompt on every message. | Medium (full text). |
| `glob` | Included when the active file matches a glob pattern. | Medium when active. |
| `model_decision` | Included when the model decides the rule is relevant. | Low (title only until selected). |
| `manual` | Included when the user explicitly invokes the rule. | Low. |

## Workflows

Workflows are repeatable prompt templates invoked with `/<workflow-name>`.

- Stored in `.windsurf/workflows/*.md`.
- Global workflows: `~/.codeium/windsurf/global_workflows/*.md`.
- System (Enterprise): `/Library/Application Support/Windsurf/workflows/*.md` (macOS), `/etc/windsurf/workflows/*.md` (Linux), `C:\ProgramData\Windsurf\workflows\*.md` (Windows).
- Precedence: System > Workspace > Global > Built-in.
- Workflows are manual-only. Use skills if the model should invoke a procedure automatically.

## App Deploys

Cascade can deploy web apps to Netlify directly from Devin Desktop.

- Creates a public URL at `<subdomain>.windsurf.build`.
- Writes a `windsurf_deployment.yaml` file to the project root for redeployment.
- Supports Next.js, React, Vue, Svelte, and static HTML/CSS/JS.
- Not available with Devin Local.
- Intended for preview, not production.

Rate limits:

| Plan | Deployments per day | Max unclaimed sites |
|------|--------------------|---------------------|
| Free | 1 | 1 |
| Pro  | 10 | 5 |
