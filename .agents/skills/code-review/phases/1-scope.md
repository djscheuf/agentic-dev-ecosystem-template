# Phase 1: Scope

**Goal**: Establish what is being reviewed. Requirements first, from documentation; then the actual changes on the branch.

**Produces**: `identified_requirements` and `impacted_scope` in the output.

## Step A: Identify the requirements (documentation first)
Look in this order, stopping when you have the story or stories:
1. Anything the user supplied (paths, ticket ids, pasted text).
2. PR description (`gh pr view` if available and the branch has a PR).
3. Branch name and commit messages (ticket ids, story references).
4. Repo documentation: `docs/`, `specs/`, `README`, ADRs, feature files, acceptance-criteria files, changelogs.
5. Ask the user. If they confirm none exist, infer requirements from the PR description and commits, and record a `blocking` comment of type `story` stating that the change has no stated requirement.

For each requirement record: an identifier or title, a one-line intent, the acceptance criteria if present, and its source.

## Step B: Identify the changes
1. Find the base: `git merge-base HEAD <default-branch>`. Use the PR base if one exists.
2. Survey: `git diff --stat <base>...HEAD`, `git log --oneline <base>..HEAD`.
3. Note uncommitted changes (`git status`) and ask whether they are in scope.
4. Group changed files by concern or layer (UI, API, data, config, tests, docs, build).
5. Read the diff with the requirements in mind. For each group, state in a line what it is for.

## Step C: Derive the impacted scope
List:
- **Directly changed**: modules, components, endpoints, tables, configs.
- **Dependents**: callers and consumers of changed code (search for usages).
- **Contracts touched**: public APIs, schemas, migrations, events, config keys, feature flags.
- **Behaviors and workflows affected**: in user terms, not file terms.

## Scope-level checks (record as comments when found)
- **Size**: a diff over roughly 300 to 400 changed lines is hard to review well. Comment (type `design` or `implementation`) suggesting it be split, but still review it.
- **Mixed concerns**: a feature, a bug fix, and a refactor in one change. Comment and recommend separation.
- **Unrelated changes**: changes that trace to no requirement go to Phase 2.
- **Missing context**: if you cannot tell why the change exists, ask the user rather than guessing.

## Before leaving this phase
You can state, in two sentences, what the change is meant to achieve and what it touches. If not, keep scoping.
