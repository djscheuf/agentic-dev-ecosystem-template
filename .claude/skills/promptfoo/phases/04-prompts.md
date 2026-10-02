# Phase 4: Prompt Configuration

promptfoo supports several ways to define prompts, from simple strings to dynamic functions.

## Text Prompts

```yaml
prompts:
  - 'Translate the following to {{language}}: {{input}}'
  - 'Summarize this article: {{article}}'
```

Variables are substituted with `{{varName}}`. Multiline strings are supported with YAML `|`:

```yaml
prompts:
  - |
    You are a helpful assistant.
    User: {{input}}
    Assistant:
```

## File-Based Prompts

```yaml
prompts:
  - file://prompts/customer_service.txt
  - file://prompts/technical_support.md
  - file://prompts/*.txt
```

Supported formats:

- `.txt` — plain text
- `.md` — Markdown (content used as-is)
- `.j2` — Jinja2 templates (not Nunjucks, but supported)
- `.csv` — multiple prompts with `prompt` and `label` columns

Multiple prompts in one file are separated by `---`:

```text
Translate to French: {{text}}
---
Translate to Spanish: {{text}}
```

## Chat Format (JSON)

Use a JSON array of messages for chat models:

```json
[
  { "role": "system", "content": "You are a helpful coding assistant." },
  { "role": "user", "content": "Write a function to {{task}}" }
]
```

Reference it from config:

```yaml
prompts:
  - file://chat_prompt.json
```

Multi-turn conversations include `assistant` messages:

```json
[
  { "role": "system", "content": "You are a tutoring assistant." },
  { "role": "user", "content": "What is recursion?" },
  { "role": "assistant", "content": "Recursion is a function that calls itself." },
  { "role": "user", "content": "Show me an example in {{language}}." }
]
```

## Dynamic Prompts (Functions)

Generate prompts with JavaScript or Python based on variables and provider.

### JavaScript

```javascript
// generate_prompt.js
module.exports = async function ({ vars, provider }) {
  const complexity = vars.complexity || 'medium';
  if (complexity === 'simple') {
    return `Explain ${vars.topic} in simple terms.`;
  }
  return `Provide a detailed explanation of ${vars.topic} with examples.`;
};
```

```yaml
prompts:
  - file://generate_prompt.js
```

### Python

```python
# generate_prompt.py
def create_prompt(context):
    vars = context['vars']
    if vars.get('technical_audience'):
        return f"Provide a technical analysis of {vars['topic']}"
    return f"Explain {vars['topic']} for beginners"
```

```yaml
prompts:
  - file://generate_prompt.py:create_prompt
```

### Returning Provider Config

A dynamic prompt can also return per-call provider config:

```javascript
module.exports = async function ({ vars }) {
  return {
    prompt: `Analyze ${vars.topic}`,
    config: {
      temperature: vars.creative ? 0.9 : 0.3,
      max_tokens: vars.detailed ? 1000 : 200,
    },
  };
};
```

## Nunjucks Templates

promptfoo uses Nunjucks for variable substitution. Supported features:

- Variables: `{{var}}`
- Conditionals: `{% if premium %}...{% endif %}`
- Loops: `{% for item in items %}...{% endfor %}`
- Filters: `{{name | upper}}`
- Custom filters via `nunjucksFilters`

### Custom Filters

```javascript
// uppercase_first.js
module.exports = function (str) {
  return str.charAt(0).toUpperCase() + str.slice(1);
};
```

```yaml
nunjucksFilters:
  uppercaseFirst: ./uppercase_first.js

prompts:
  - 'Dear {{ name | uppercaseFirst }}, {{ message }}'
```

### Object Variables in Templates

Objects passed as vars are stringified by default. To access a property, use dot notation or the `json` filter:

```yaml
# vars: user: { name: Alice }
prompts:
  - 'Hello {{ user.name }}'
  - 'User data: {{ user | json }}'
```

If you see `[object Object]`, you are using an object variable without property access or a filter.

## Prompt Labels and IDs

Label prompts for easier filtering and reporting:

```yaml
prompts:
  - id: file://customer_prompt.txt
    label: Customer Service
  - id: file://technical_prompt.txt
    label: Technical Support
```

## Default Prompt

If no `prompts` are specified, promptfoo uses `{{prompt}}` as a passthrough. This is useful when the input itself is the prompt.

## Executable Scripts

You can also use an executable script as a prompt:

```yaml
prompts:
  - exec: python generate_prompt.py
```

Use sparingly; dynamic prompt functions are usually cleaner.

## Next Step

- Providers: `phases/05-providers.md`
