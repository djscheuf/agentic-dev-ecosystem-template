---
name: promptfoo
description: Context-efficient reference for building, configuring, and optimizing promptfoo evals, providers, and assertions locally. Use this skill before writing or debugging promptfoo-related configs and custom scripts.
generated: 202607151400
---

# Promptfoo Knowledge Skill

Use this skill when the task involves creating, editing, or debugging promptfoo configuration (`promptfooconfig.yaml`), providers, custom evaluation scripts, or CLI workflows.

## When to Run

- Setting up a new promptfoo eval or project
- Configuring providers (built-in, local, or custom)
- Writing or debugging custom JavaScript/TypeScript/Python providers
- Writing or debugging custom assertions or transforms
- Optimizing prompts or comparing models
- Troubleshooting failed evals, provider errors, or OOM/timeouts
- Converting between CLI, YAML, and Node-package usage

## What Promptfoo Is

promptfoo is an open-source CLI and library for evaluating and red-teaming LLM applications. It runs prompts against one or more providers (LLM APIs), compares outputs, and scores them with assertions and metrics. The core idea is **test-driven prompt engineering**: define expectations first, then iterate.

## Mental Model

```
prompts × providers × tests = matrix of outputs
                |
                v
        assertions & metrics
```

- **Prompts**: text, chat JSON, or dynamically generated templates
- **Providers**: LLM targets (OpenAI, Anthropic, local Ollama, custom JS/Python, HTTP, etc.)
- **Tests**: input variables + assertions that define pass/fail criteria
- **Config**: a single `promptfooconfig.yaml` binds them together

## Phase Map

Read phases in order when learning the tool; jump directly to a phase when the task is focused.

| Phase | File | Covers |
|-------|------|--------|
| 0 | `SKILL.md` | Index, when-to-use, mental model (you are here) |
| 1 | `phases/01-overview.md` | Philosophy, workflow, key concepts |
| 2 | `phases/02-quickstart-workflow.md` | Install, init, eval, view, .env |
| 3 | `phases/03-config-reference.md` | `promptfooconfig.yaml` structure and properties |
| 4 | `phases/04-prompts.md` | Text, file, chat, dynamic, Nunjucks |
| 5 | `phases/05-providers.md` | Built-in providers, syntax, configuration, env vars |
| 6 | `phases/06-assertions-metrics.md` | Deterministic, model-graded, custom, derived, named |
| 7 | `phases/07-custom-providers.md` | JS/TS/Python provider interfaces and return contracts |
| 8 | `phases/08-evaluation-scripts.md` | Custom asserts, transforms, Node package API |
| 9 | `phases/09-cli-commands.md` | CLI commands, environment variables, CI behavior |
| 10 | `phases/10-debugging-scenarios.md` | Troubleshooting, logs, OOM, stuck evals, custom-provider debugging |
| QR | `quick-reference.md` | Compact cheat sheet |

## Quick Decision Guide

- **New eval?** Start at `phases/02-quickstart-workflow.md`, then `phases/03-config-reference.md`.
- **Need a custom model/API?** Read `phases/07-custom-providers.md`.
- **Need a custom scorer?** Read `phases/08-evaluation-scripts.md`.
- **Something is broken?** Read `phases/10-debugging-scenarios.md` first.
- **Need a property list?** Read `phases/03-config-reference.md` or `quick-reference.md`.
