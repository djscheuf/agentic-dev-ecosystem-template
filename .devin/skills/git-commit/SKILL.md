---
name: git-commit
description: Create conventional commits in this repository based on observed main-branch style and Karma commit message conventions.
---

# Git Commit Skill

## TL;DR
- First line format: `type(scope): subject` (preferred) or `type(scope)` for very short, self-describing changes.
- First line ≤ 72 characters.
- Lowercase type and scope.
- Imperative, present-tense subject.
- Optional body and footer separated by blank lines.
- ALWAYS keep commit messages about the changes, not the tooling.

## Absolute rules

### No AI/tooling attribution

Commit messages describe the change, not who or what wrote it. Only the human author is accountable for commits in this repository. The message body and footer MUST NOT contain any AI/tooling attribution or provenance markers.

Forbidden content includes, but is not limited to:

- `Generated with [Devin](...)` or any similar tool citation
- `Co-Authored-By: Devin <...>`
- `Signed-off-by:` inserted by an assistant
- `Reviewed-by:` or similar trailers added by tooling
- Any footer line containing a URL to an AI assistant or automation platform

Before committing, grep the drafted message for the patterns above. If any are present, delete them.

## Message format

Preferred:

Short, self-describing changes use the observed repo style:
```
<type>(<scope>): <light details>
```


Use this sparingly; prefer a colon and subject for anything non-trivial.
```
<type>(<scope>): <subject>
<BLANK LINE>
<body>
<BLANK LINE>
<footer>
```

## Allowed types

The main branch uses these type prefixes. Prefer them in this order:

| Type | Use when |
|---|---|
| `feat` | A new feature or capability. |
| `fix` | A bug fix or correction. |
| `doc` | Documentation or ADR/vault changes. This repo uses `doc`, not `docs`. |
| `clean` | Removing, ignoring, or tidying files and configuration. |
| `wip` | Work-in-progress checkpoint that is intentionally committed. |
| `refactor` | Code restructuring without changing external behavior. |
| `rename` | Renaming files, skills, or symbols. |
| `test` | Adding or changing tests only. |
| `tweak` | A small adjustment to an existing feature. |
| `maint` | Maintenance, dependency, or tooling updates. |

Avoid inventing new types. For changes that legitimately span multiple concerns, join types with a slash: `type(scope)/type(scope): subject`.

## Scope

The scope is a short phrase describing the area affected. It may be a skill name, component, file, or concept. Scopes in this repo often contain spaces and read as a short description.

Examples from main branch:
- `feat(verify scrips to discover and execute tests)`
- `fix(tdd related skills)`
- `refactor(extract rubric weights)`
- `doc(link back to vault protocol origins)`
- `rename(expand-intent to expand-analysis)`

Keep the scope meaningful and no longer than necessary.

## Subject

- Start with an imperative verb: `add`, `fix`, `update`, `refactor`, `remove`.
- Do not end with a period.
- Use present tense: `change` not `changed` or `changes`.
- Keep the first line under 72 characters.

Examples:
- `feat(workstream skill)`
- `fix(tdd related skills): improve tracking of test case document`
- `refactor(extract rubric weights): makes it easier to adjust rubric weighting when needed later`
- `doc(adr for skill input coupling)`

## Body

Use the body to explain motivation and contrast with previous behavior. Use imperative, present tense. Wrap lines at 72 characters when possible. Keep it short and factual.

## Footer

- `Closes #123` (one or more issues, comma-separated)
- `BREAKING CHANGE: <description and migration notes>`


## Commit creation workflow

1. **Review changes** before staging.
   Run in parallel:
   - `git status`
   - `git diff`
   - `git log`

2. **Stage files** using the repository owner's preferred method.
   Common options:
   - `git add -p` to review hunks individually.
   - `git add <file>` for specific files.
   - `git add -A` only when all changes belong in one commit.

   > **Note for the owner:** Add your preferred staging instructions here (e.g., `git add -p` vs. `git add <file>` vs. a shell alias).

3. **Draft the message** using the format above. Focus on *why*, not *what*.

4. **Scan the draft for forbidden attribution.** Run a quick check on the message you are about to commit:

   ```bash
   cat <<'MSG' | grep -iE 'Generated with|Co-Authored-By:|Signed-off-by:|Reviewed-by:|devin\.ai'
   <paste your drafted message here>
   MSG
   ```

   If the grep returns any matches, remove those lines before proceeding. This step is mandatory; the project will reject commits that contain AI/tooling attribution.

5. **Commit** using a here-doc so the message can contain blank lines:

```bash
git commit -m "$(cat <<'EOF'
<type>(<scope>): <subject>

<body>
EOF
)"
```

6. **Verify** the result:

   ```bash
   git log --oneline -5
   git log -1 --format='%B%n---%n%(trailers)'
   ```

   Confirm that no forbidden attribution trailers appear in the body or footer.

## PR merge commits

Pull-request merge commits on main use a different, GitHub-generated style: `Type/scope description (#N)`. Examples:
- `Test/grade design (#8)`
- `Maint/edd providers and patterns (#7)`

Do not use this style for regular commits.

## Examples from main branch

```
feat(verify scrips to discover and execute tests)/clean(split implement and sub-tdd loop to attempt context control)
fix(tdd related skills): improve tracking of test case document
refactor(extract rubric weights): makes it easier to adjust rubric weighting when needed later
doc(link back to vault protocol origins)
wip(tweak audit skill description)
clean(add gitignore to support dev testing)
rename(analyze workflow to SDLC): map name to what the workflow is actually doing for a given story
tweak(extract skill): limit what is in initial story schema, depend on shell only
```

## Common mistakes

- Capitalizing the type: use `feat`, not `Feat`.
- Using `docs` instead of `doc`.
- Ending the subject with a period.
- Exceeding 72 characters on the first line.
- Forgetting a blank line between subject and body.
- Using PR merge style (`Type/scope description (#N)`) for normal commits.
- Including AI/tooling attribution ("Generated with ...", "Co-Authored-By: ...", "Signed-off-by: ...", "Reviewed-by: ...", etc.) in the body or footer. This is the most common machine-generated mistake and is explicitly forbidden — remove these lines before committing.

## Notes

This convention is derived from the main branch commit history and aligns with the Karma/Angular commit message format where practical. The repo accepts a broader set of type prefixes and multi-type subjects than strict Karma.
