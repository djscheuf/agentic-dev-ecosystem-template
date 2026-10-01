# Quick Reference: Promptfoo

Compact lookup for common properties, commands, and patterns.

## Config File Skeleton

```yaml
description: My eval

prompts:
  - 'Translate to {{language}}: {{input}}'

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
```

## Common CLI Commands

```bash
promptfoo init
promptfoo eval
promptfoo eval -c my.yaml -j 4 --no-cache
promptfoo view
promptfoo optimize
promptfoo validate config
promptfoo cache clear
promptfoo logs --list
promptfoo debug -c my.yaml
```

## Provider Syntax

```yaml
# Simple string
providers:
  - openai:chat:gpt-5-mini
  - anthropic:messages:claude-opus-4-6
  - ollama:chat:llama3.3

# Object with config
providers:
  - id: openai:chat:gpt-5-mini
    label: fast
    config:
      temperature: 0.7
      max_tokens: 150

# Custom provider
providers:
  - file://custom_provider.js
  - id: file://custom_provider.py
    label: my-python-provider
```

## Common Provider Config

| Option | Description |
|--------|-------------|
| `temperature` | Randomness (0-1) |
| `max_tokens` / `max_completion_tokens` / `max_output_tokens` | Token limits |
| `top_p` | Nucleus sampling |
| `frequency_penalty` / `presence_penalty` | Penalties |
| `stop` | Stop sequences |
| `seed` | Deterministic seed |
| `apiKey` / `apiKeyEnvar` | Auth |
| `apiBaseUrl` / `apiHost` | Custom endpoint |
| `headers` | Extra HTTP headers |
| `maxRetries` | Retries |
| `passthrough` | Provider-specific extra fields |

## Prompt Formats

```yaml
prompts:
  # Text
  - 'Translate: {{text}}'
  # File
  - file://prompt.txt
  # Chat JSON
  - file://chat.json
  # Dynamic JS
  - file://generate_prompt.js
  # Dynamic Python
  - file://generate_prompt.py:fn_name
```

## Assertion Types

### Deterministic

`equals`, `contains`, `icontains`, `contains-any`, `contains-all`, `icontains-any`, `icontains-all`, `regex`, `starts-with`, `is-json`, `contains-json`, `is-html`, `contains-html`, `is-sql`, `contains-sql`, `is-xml`, `contains-xml`, `is-refusal`, `javascript`, `python`, `webhook`, `latency`, `cost`, `finish-reason`, `levenshtein`, `rouge-n`, `bleu`, `gleu`, `meteor`, `perplexity`, `perplexity-score`, `classifier`, `select-best`, `word-count`, `assert-set`.

Negate any with `not-` prefix (e.g., `not-contains`).

### Model-Assisted

`llm-rubric`, `model-graded-closedqa`, `factuality`, `similar`, `classifier`, `moderation`, `g-eval`, `answer-relevance`, `context-faithfulness`, `context-recall`, `context-relevance`, `conversation-relevance`, `trajectory:goal-success`, `pi`, `max-score`.

### Assertion Examples

```yaml
assert:
  - type: contains
    value: 'expected text'
  - type: is-json
    value: file://schema.json
  - type: latency
    threshold: 5000
  - type: llm-rubric
    value: Is clear and concise
    provider: openai:gpt-5-mini
  - type: similar
    value: 'expected meaning'
    threshold: 0.8
```

## Test Case Properties

```yaml
tests:
  - description: Name
    vars:
      key: value
    assert: [...]
    options:
      provider: openai:gpt-5-mini
      repeat: 2
      transform: output.toLowerCase()
    metadata:
      category: x
    threshold: 0.8
    providers:
      - fast-model
```

## `defaultTest`

```yaml
defaultTest:
  vars:
    audience: developer
  assert:
    - type: llm-rubric
      value: Does not describe itself as an AI
  options:
    provider: openai:gpt-5-mini
```

## Derived Metrics

```yaml
derivedMetrics:
  - name: f1_score
    value: '2 * precision * recall / (precision + recall)'
```

## Environment Variables

```bash
OPENAI_API_KEY=...
ANTHROPIC_API_KEY=...
OLLAMA_BASE_URL=http://localhost:11434
PROMPTFOO_CACHE_ENABLED=true
PROMPTFOO_LOG_DIR=./logs
PROMPTFOO_EVAL_TIMEOUT_MS=30000
PROMPTFOO_MAX_EVAL_TIME_MS=300000
PROMPTFOO_PYTHON=/usr/local/bin/python3
PROMPTFOO_PYTHON_DEBUG_ENABLED=true
LOG_LEVEL=debug
```

## Custom JS Provider Contract

```javascript
export default class MyProvider {
  id = () => 'my-provider';
  callApi = async (prompt, context, options) => ({
    output: '...',
    tokenUsage: { total: 100, prompt: 50, completion: 50 },
    cost: 0.002,
    error: undefined,
  });
}
```

## Custom Python Provider Contract

```python
def call_api(prompt, options, context):
    return {
        "output": "...",
        "tokenUsage": {"total": 100, "prompt": 50, "completion": 50},
        "cost": 0.002,
    }
```

## Custom Assertion Return

```javascript
return {
  pass: true,
  score: 0.75,
  reason: 'Looks good',
  componentResults: [...],
};
```

```python
return {
    'pass': True,
    'score': 0.75,
    'reason': 'Looks good',
    'component_results': [...],
}
```
