# Phase 8: Evaluation Scripts and Node Package

Custom scripts let you implement custom assertions, transforms, and dynamic prompts. You can also use promptfoo as a Node library.

## Custom JavaScript Assertions

### Inline

```yaml
assert:
  - type: javascript
    value: output.toLowerCase().includes('bananas')
```

### Multiline

```yaml
assert:
  - type: javascript
    value: |
      if (output === 'Expected output') {
        return { pass: true, score: 0.5 };
      }
      return { pass: false, score: 0, reason: 'Assertion failed' };
```

### External File

```yaml
assert:
  - type: javascript
    value: file://relative/path/to/script.js
    config:
      maximumOutputSize: 10
```

Specify a named function:

```yaml
assert:
  - type: javascript
    value: file://relative/path/to/script.js:customFunction
```

The file must export a function taking `(output, context)`:

```javascript
module.exports = (output, context) => {
  return output.length <= context.config.maximumOutputSize;
};
```

### Return Types

- `boolean` — pass/fail
- `number` — score (0 = fail, higher is better)
- `GradingResult` — full result object

```javascript
return {
  pass: true,
  score: 0.75,
  reason: 'Looks good to me',
  componentResults: [
    { pass: true, score: 0.5, reason: 'Contains banana' },
    { pass: true, score: 0.5, reason: 'Contains yellow' },
  ],
};
```

### Context for JavaScript Assertions

```javascript
{
  prompt: string | undefined;
  vars: Record<string, string | object>;
  test: AtomicTestCase;
  logProbs: number[] | undefined;
  config?: Record<string, any>;
  provider: ApiProvider | undefined;
  providerResponse: ProviderResponse | undefined;
  trace?: TraceData;
  metadata?: Record<string, any>;
}
```

## Custom Python Assertions

### Inline

```yaml
assert:
  - type: python
    value: 'len(output) > 10'
```

### External File

```yaml
assert:
  - type: python
    value: file://relative/path/to/script.py
    config:
      outputLengthLimit: 10
```

Named function:

```yaml
assert:
  - type: python
    value: file://relative/path/to/script.py:custom_assert
```

Default function name is `get_assert`.

```python
from typing import Dict, Union

def get_assert(output: str, context) -> Union[bool, float, Dict[str, any]]:
    return {
        'pass': True,
        'score': 0.6,
        'reason': 'Looks good to me',
    }
```

### GradingResult Mapping

Python snake_case keys are mapped to camelCase:

- `pass_` / `'pass'` → `pass`
- `named_scores` → `namedScores`
- `component_results` → `componentResults`
- `tokens_used` → `tokensUsed`

### Context for Python Assertions

Same shape as JavaScript, available as `context['vars']`, `context['prompt']`, `context['providerResponse']`, etc.

## Transforms

Transforms modify the output before it is graded. They can be defined at test, assertion, or global level.

```yaml
tests:
  - vars:
      question: 'What is 2+2?'
    options:
      transform: output.toLowerCase()
    assert:
      - type: contains
        value: 'four'
```

Transforms can be JavaScript/Python expressions or functions:

```yaml
tests:
  - options:
      transform: file://transform.js
```

Execution order: global → test → assertion.

## Node Package API

Install:

```bash
npm install promptfoo
```

Basic usage:

```javascript
import promptfoo from 'promptfoo';

const evalRecord = await promptfoo.evaluate(
  {
    prompts: ['Rephrase in French: {{body}}'],
    providers: ['openai:gpt-5-mini'],
    tests: [
      { vars: { body: 'Hello world' } },
      { vars: { body: "I'm hungry" } },
    ],
    writeLatestResults: true,
  },
  { maxConcurrency: 2 },
);

const results = await evalRecord.toEvaluateSummary();
console.log(results);
```

### Function-Based Providers and Assertions

```javascript
await promptfoo.evaluate({
  prompts: [
    'Rephrase in French: {{body}}',
    (vars) => `Rephrase like a pirate: ${vars.body}`,
  ],
  providers: [
    'openai:gpt-5-mini',
    (prompt, context) => {
      return { output: '<LLM output>' };
    },
  ],
  tests: [
    {
      vars: { body: 'Hello world' },
      assert: [
        {
          type: 'javascript',
          value: (output) => ({
            pass: output.includes("J'ai faim"),
            score: output.includes("J'ai faim") ? 1 : 0,
            reason: 'Output contained substring',
          }),
        },
      ],
    },
  ],
});
```

### Loading Providers Programmatically

```javascript
import { loadApiProvider } from 'promptfoo';

const provider = await loadApiProvider('openai:o3-mini');
const providerWithOptions = await loadApiProvider('azure:chat:test', {
  options: { apiHost: 'test-host', apiKey: 'test-key' },
});
```

## Extension Hooks

Register hooks for lifecycle events:

```yaml
extensions:
  - file://hooks.js:afterAll
```

Common hooks: `beforeAll`, `afterAll`, `beforeEach`, `afterEach`, `beforeEachTest`, `afterEachTest`. Useful for setup/teardown and custom reporting.

## Next Step

- CLI commands and environment variables: `phases/09-cli-commands.md`
