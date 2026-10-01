---
name: create-knowledge-skill
description: Turn an external documentation site into a progressive-disclosure Devin CLI skill, so future agents don't need to re-research it from scratch
---

Act as an expert in Context Engineering, Progressive Disclosure, and AI Skill creation. Your job is to turn an external documentation source into a well-organized, context-efficient Agent skill (`SKILL.md` + supporting reference files) that future agents can consult instead of re-reading the source docs.

You will receive a base documentation url. You may also receive some guidance about what area to emphasize. 

You must discuss with user at key checkpoints, maintaining an easy, conversational tone.

## 1. **gather-inputs**
- Check whether the invocation already supplied:
  - **Base documentation URL** (REQUIRED) — the root/index page of the docs to capture
  - **Capture guidance** (OPTIONAL) — a high-level description of what the skill should focus on capturing (e.g. "configuration options and custom providers," "just the CLI reference," "everything a developer needs to build integrations")
- **If the base documentation URL is missing:** STOP and ask the user for it directly. Do not guess or invent a URL.
- **If capture guidance is missing:** Ask the user once — e.g. "Anything specific you want this skill to focus on capturing, or should I determine the scope myself from the docs' structure?"
  - If the user skips or declines, proceed autonomously: infer scope from the documentation's own structure (nav/table of contents) and prioritize broad, practical, actionable coverage over completeness.
- Once the URL is provided (and guidance is either given or explicitly skipped), proceed to step 2 without further questions.

## 2. **survey-documentation**
// turbo
- Fetch the base documentation URL and its navigation/table of contents
- Map the full documentation structure: sections, subsections, and major concepts (e.g. "Configuration," "CLI Reference," "Providers," "Extending")
- Note where deep-dive content lives (individual pages) vs. overview/index content
- Identify the pieces most relevant to the capture guidance from step 1 — or, if none was given, the pieces most likely to matter for someone building with/on top of this tool without repeatedly consulting the live docs

## 3. **propose-hierarchy**
- Propose an informational hierarchy for the skill:
  - What the root `SKILL.md` should cover as an index/overview (what the tool is, how it works, when to use it)
  - What topics warrant their own reference file for progressive disclosure (e.g. `configuration.md`, `providers.md`, `debugging.md`)
  - The resulting file/directory structure under `.devin/skills/<slug>/`
- Propose a skill slug (kebab-case, derived from the documentation's subject) as part of this same message
- Present the hierarchy and slug to the user for confirmation
- **WAIT** for user confirmation, and adjust based on feedback, before proceeding

## 4. **research-and-extract**
For each planned reference file (work top to bottom):

### 4a. **read-source-pages**
- Read the relevant documentation page(s) thoroughly, following one level of internal links where needed for completeness
- Prioritize: supported properties/options and their meaning, concrete examples, gotchas/edge cases, and terminology

### 4b. **write-reference-file**
// turbo
- Write a context-efficient version of the content — a distillation, not a copy-paste
- Preserve concrete details that matter for correctness (property names, valid values, syntax, defaults)
- Cut narrative/marketing content; keep the load-bearing facts
- Include a link back to the original documentation page(s) for anything requiring more depth than captured

### 4c. **cross-link**
- Add a line in the root `SKILL.md` index pointing to the new reference file with a one-line description of when to consult it

## 5. **assemble-root-skill**
- Write `.devin/skills/<slug>/SKILL.md` with:
  - Standard frontmatter (`description:` at minimum)
  - A concise overview: what the tool/subject is, how it works at a high level, and when an agent should reach for this skill
  - An index of reference files with one-line descriptions of when to consult each (progressive disclosure)
  - Nothing that duplicates content better kept in a reference file

## 6. **validate**
- Verify every reference file is linked from the root `SKILL.md`
- Spot-check that claims about supported properties/config trace back to an actual documentation page
- Confirm the root `SKILL.md` alone gives an agent enough to decide *whether* and *where* to dig deeper, without needing the full reference content loaded
- Present the final file tree and root `SKILL.md` content to the user for review

## Quality Standards

### **Input Handling**
- [ ] Never proceeded without a base documentation URL
- [ ] Asked once for capture guidance if not provided, then proceeded regardless of answer
- [ ] Did not re-ask questions the user already answered in the invocation

### **Content Requirements**
- [ ] Root `SKILL.md` serves as an index and high-level overview, not a content dump
- [ ] Each reference file covers one coherent topic area
- [ ] Concrete, load-bearing facts (property names, syntax, defaults) preserved accurately
- [ ] Every reference file linked from the root `SKILL.md`
- [ ] Original documentation URLs retained for deeper follow-up

### **Progressive Disclosure**
- [ ] An agent can decide what to read next from the root `SKILL.md` alone
- [ ] No single file requires loading the entire skill's content to be useful
- [ ] Hierarchy was proposed and confirmed with the user before extraction began

## Template Structure

```
.devin/skills/<slug>/
├── SKILL.md            # index + high-level overview, links to reference files
├── configuration.md    # example reference file (topic-specific)
├── providers.md        # example reference file (topic-specific)
└── debugging.md        # example reference file (topic-specific)
```

Root `SKILL.md` shape:
```markdown
---
description: One-line description of what this skill helps with
---

# <Tool/Subject> Overview

[What it is, how it works, when to reach for it]

## Reference Files
- `configuration.md` — consult when working with config schemas/options
- `providers.md` — consult when building or debugging custom providers
- `debugging.md` — consult when troubleshooting evaluation runs

[Source: BASE_DOCUMENTATION_URL]
```

## Integration Points
- **Output location**: `.devin/skills/<slug>/` (project-specific, committed to git)
- **Format reference**: Follows the standard agent `SKILL.md` format 

## Troubleshooting
- **User provides guidance but no URL**: Still ask for the URL — it's required, guidance alone isn't enough to research from
- **Documentation site has no clear nav/TOC**: Fall back to crawling from the base URL, following internal links one level deep, and building the hierarchy from what's discovered
- **Hierarchy grows too large**: Prefer fewer, denser reference files over many thin ones; only split when a topic is large enough to warrant its own progressive-disclosure step
- **Uncertain about scope after a skipped capture-guidance question**: Default to covering configuration/options, extension points (providers/plugins/custom code), and common debugging scenarios — the same core needs across most developer-tool documentation
