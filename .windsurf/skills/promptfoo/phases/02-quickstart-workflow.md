# Phase 2: Quickstart Workflow

## Installation

Requires Node.js `^20.20.0` or `>=22.22.0`. Node.js 24 LTS is recommended.

```bash
# npm (global)
npm install -g promptfoo

# npx (no install)
npx promptfoo@latest

# Homebrew (Mac/Linux)
brew install promptfoo

# As a library
npm install promptfoo
```

Verify:

```bash
promptfoo --version
# or
npx promptfoo@latest --version
```

## First Eval

### 1. Initialize

```bash
promptfoo init
# or with an example
npx promptfoo@latest init --example getting-started
```

This creates `promptfooconfig.yaml` (and optionally `README.md` and prompt files).

### 2. Configure

A minimal config:

```yaml
prompts:
  - 'Translate the following to {{language}}: {{input}}'

providers:
  - openai:chat:gpt-5-mini
  - anthropic:messages:claude-opus-4-6

tests:
  - vars:
      language: French
      input: Hello world
    assert:
      - type: icontains
        value: 'Bonjour'
  - vars:
      language: Spanish
      input: Where is the library?
    assert:
      - type: icontains
        value: 'biblioteca'
```

### 3. Run

```bash
# Read promptfooconfig.yaml in current directory
promptfoo eval

# Use a different config
promptfoo eval -c my-config.yaml
```

### 4. View Results

```bash
# Interactive web UI
promptfoo view

# Or export
promptfoo eval --output results.json
```

## Common CLI Variations

```bash
# Override providers on the fly
promptfoo eval -r openai:gpt-5-mini -r ollama:chat:llama3.3

# Override prompts
promptfoo eval -p file://prompts/*.txt

# Override tests
promptfoo eval -t file://tests.yaml

# Concurrency and repeat
promptfoo eval -j 4 --repeat 3

# Disable cache for fresh calls
promptfoo eval --no-cache

# Watch for changes
promptfoo eval -w
```

## Environment Variables

promptfoo loads `.env` from the current working directory. Typical keys:

```bash
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-...
OLLAMA_BASE_URL=http://localhost:11434
```

You can also pass keys inline in the provider `config` (not recommended for committed configs).

## Web UI Setup

Alternative to `init`:

```bash
promptfoo eval setup
```

This opens a browser-based flow to create prompts, providers, and test cases.

## Next Step

- To understand the full config schema, read `phases/03-config-reference.md`.
- To learn about prompts specifically, read `phases/04-prompts.md`.
