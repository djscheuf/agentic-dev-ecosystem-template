# Phase 7: Custom Providers

Custom providers let you integrate any API or custom logic into promptfoo. Supported formats: JavaScript, TypeScript, Python, HTTP/HTTPS, WebSocket, and exec scripts.

## JavaScript / TypeScript Provider

A custom provider must implement at minimum an `id()` method and a `callApi()` method.

### Minimal Example

```javascript
// echoProvider.mjs
export default class EchoProvider {
  id = () => 'echo';

  callApi = async (prompt, context, options) => {
    return {
      output: `Echo: ${prompt}`,
    };
  };
}
```

```yaml
providers:
  - id: file://echoProvider.mjs
```

### With Constructor

```javascript
const promptfoo = require('promptfoo').default;

module.exports = class OpenAIProvider {
  constructor(options) {
    this.providerId = options.id || 'openai-custom';
    this.config = options.config;
  }

  id() {
    return this.providerId;
  }

  async callApi(prompt, context, options) {
    const { data } = await promptfoo.cache.fetchWithCache(
      'https://api.openai.com/v1/chat/completions',
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${process.env.OPENAI_API_KEY}`,
        },
        body: JSON.stringify({
          model: this.config?.model || 'gpt-5-mini',
          messages: [{ role: 'user', content: prompt }],
          max_completion_tokens: this.config?.max_tokens || 1024,
          temperature: this.config?.temperature || 1,
        }),
      },
    );

    return {
      output: data.choices[0].message.content,
      tokenUsage: data.usage,
    };
  }
};
```

### ProviderResponse Contract

`callApi` must return an object with these fields:

```javascript
{
  output: 'Model response text or structured data',
  error: 'Error message if applicable',           // optional
  prompt: 'The actual prompt sent to the LLM',    // optional, shown in UI
  tokenUsage: { total: 100, prompt: 50, completion: 50 }, // optional
  cost: 0.002,                                    // optional
  cached: false,                                  // optional
  latencyMs: 150,                                 // optional
  conversationEnded: false,                       // optional (multi-turn redteam)
  conversationEndReason: 'thread_closed',         // optional
  metadata: {},                                   // optional
}
```

### Context Parameter

`context` contains test case information and utilities:

```javascript
{
  vars: {},              // Test case variables
  prompt: {},            // Prompt template (raw, label, config)
  test: {                // Full test case
    vars: {},
    metadata: {
      pluginId: '...',   // Redteam plugin
      strategyId: '...',   // Redteam strategy
    },
  },
  originalProvider: {},  // Original provider when overridden
  logger: {},            // Winston logger
}
```

### TypeScript Example

```typescript
import promptfoo from 'promptfoo';
import type { ApiProvider, ProviderOptions, ProviderResponse, CallApiContextParams } from 'promptfoo';

export default class TypedProvider implements ApiProvider {
  protected providerId: string;
  public config: Record<string, any>;

  constructor(options: ProviderOptions) {
    this.providerId = options.id || 'typed-provider';
    this.config = options.config || {};
  }

  id(): string {
    return this.providerId;
  }

  async callApi(prompt: string, context?: CallApiContextParams): Promise<ProviderResponse> {
    const username = (context?.vars?.username as string) || 'anonymous';
    return {
      output: `Hello, ${username}! You said: "${prompt}"`,
      tokenUsage: {
        total: prompt.length,
        prompt: prompt.length,
        completion: 0,
      },
    };
  }
}
```

### Additional Capabilities

JavaScript providers can also implement:

- `callEmbeddingApi` for embeddings
- `callClassificationApi` for classification
- Multimodal content handling (images, audio)

## Python Provider

### Minimal Example

```python
# echo_provider.py
def call_api(prompt, options, context):
    config = options.get('config', {})
    prefix = config.get('prefix', 'Tell me about: ')
    return {
        "output": f"{prefix}{prompt}",
    }
```

```yaml
providers:
  - id: 'file://echo_provider.py'
```

### Function Interface

Your Python script must implement one or more of these functions:

```python
def call_api(prompt: str, options: dict, context: dict) -> dict:
    pass

def call_embedding_api(prompt: str, options: dict) -> dict:
    pass

def call_classification_api(prompt: str, options: dict) -> dict:
    pass
```

Async versions (`async def`) are also supported.

### Parameters

- `prompt`: string, or JSON-encoded chat messages `[{"role": "user", "content": "..."}]`
- `options`: `{ "id": "file://...", "config": { ... } }` plus `basePath`
- `context` (only for `call_api`): `{ "vars": {}, "prompt": {}, "test": { "metadata": {} } }`

### Return Format

```python
{
    "output": "Your response here",
    "tokenUsage": {"total": 150, "prompt": 50, "completion": 100},
    "cost": 0.0025,
    "cached": False,
    "latencyMs": 150,
    "conversationEnded": False,
    "conversationEndReason": "thread_closed",
    "error": "Description of what went wrong",
}
```

### Configuration

```yaml
providers:
  - id: file://./my_provider.py
    label: 'My Custom API'
    config:
      model: 'gpt-5'
      temperature: 0.7
      max_tokens: 2000
```

You can also set a per-provider Python executable:

```yaml
providers:
  - id: 'file://my_provider.py'
    config:
      pythonExecutable: /path/to/specific/python
```

## HTTP/HTTPS Provider

```yaml
providers:
  - id: https://api.example.com/v1/chat/completions
    config:
      headers:
        Authorization: 'Bearer your_api_key'
      method: 'POST'
      body:
        model: 'my-model'
        messages: '[{"role":"user","content":"{{prompt}}"}]'
```

## WebSocket Provider

```yaml
providers:
  - id: ws://example.com/ws
    config:
      messageTemplate: '{"prompt": "{{prompt}}"}'
```

## Exec Provider

```yaml
providers:
  - 'exec: python chain.py'
```

## Caching in Custom Providers

Use the built-in cache for HTTP calls:

```javascript
const { data, cached } = await promptfoo.cache.fetchWithCache(
  url,
  { method: 'POST', body: JSON.stringify(payload) },
  5000, // timeout ms
);
```

## Multiple Instances

Reuse the same provider file with different config/labels:

```yaml
providers:
  - id: file:///path/to/provider.js
    label: high-temperature
    config:
      temperature: 0.9
  - id: file:///path/to/provider.js
    label: low-temperature
    config:
      temperature: 0.1
```

## Next Step

- Custom assertions and transforms: `phases/08-evaluation-scripts.md`
