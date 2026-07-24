# Phase 5: Providers

Providers are the interfaces to LLMs and AI services. `providers` and `targets` are interchangeable in config.

## Provider Syntax

### Simple String

```yaml
providers:
  - openai:chat:gpt-5-mini
  - anthropic:messages:claude-opus-4-6
  - ollama:chat:llama3.3
```

### Object with Config

```yaml
providers:
  - id: openai:chat:gpt-5-mini
    label: fast-model
    config:
      temperature: 0.7
      max_tokens: 150
```

### File-Based

```yaml
providers:
  - file://provider.yaml
  - file://providers.json
```

A single provider file looks like:

```yaml
id: openai:chat:gpt-5-mini
label: Foo bar
config:
  temperature: 0.9
```

A multi-provider file is an array of such objects.

## Common Configuration Options

Many providers support these fields in `config`:

| Option | Description |
|--------|-------------|
| `temperature` | Randomness (0.0-1.0) |
| `max_tokens` / `max_completion_tokens` / `max_output_tokens` | Token limits |
| `top_p` | Nucleus sampling |
| `frequency_penalty` | Penalize frequent tokens |
| `presence_penalty` | Penalize new tokens |
| `stop` | Stop sequences |
| `seed` | Deterministic seed |
| `apiKey` / `apiKeyEnvar` | Auth inline or via env var |
| `apiBaseUrl` / `apiHost` | Custom endpoint |
| `headers` | Extra HTTP headers |
| `maxRetries` | Retry count |
| `passthrough` | Provider-specific extra fields |

## Authentication Patterns

Preferred: environment variables.

```bash
export OPENAI_API_KEY=sk-...
export ANTHROPIC_API_KEY=sk-...
export OLLAMA_BASE_URL=http://localhost:11434
```

Fallback: inline config.

```yaml
providers:
  - id: openai:chat:gpt-5-mini
    config:
      apiKey: sk-...
```

## Built-in Provider Examples

### OpenAI

```yaml
providers:
  - id: openai:chat:gpt-5-mini
    config:
      temperature: 0
      max_completion_tokens: 128
      apiKey: sk-abc123
```

Common OpenAI config also includes:

- `response_format` (`json_object`, `json_schema`)
- `tools`, `tool_choice`, `function_call`
- `reasoning` (for o-series)
- `inputCost`, `outputCost`, `audioInputCost`, `audioOutputCost`
- `organization`, `store`, `metadata`, `user`

### Anthropic

```yaml
providers:
  - id: anthropic:messages:claude-opus-4-6
    config:
      max_tokens: 1000
      temperature: 0.7
```

Supports tool calling, images/vision, prompt caching, citations, PDFs, extended thinking, and structured outputs.

### Ollama (Local)

```yaml
providers:
  - id: ollama:chat:llama3.3
    config:
      temperature: 0.7
      num_predict: 1024
      passthrough:
        keep_alive: '5m'
        format: 'json'
```

Environment variables:

- `OLLAMA_BASE_URL` (default `http://localhost:11434`)
- `OLLAMA_API_KEY`
- `REQUEST_TIMEOUT_MS`

Use `ollama:completion:<model>` for the `/api/generate` endpoint and `ollama:chat:<model>` for `/api/chat`. Use `ollama:embeddings:<model>` for similarity assertions.

## Custom Integration Types

| Type | Syntax | Use Case |
|------|--------|----------|
| File-based config | `file://provider.yaml` | Reusable provider definitions |
| JavaScript provider | `file://custom_provider.js` | Custom JS/TS logic |
| Python provider | `id: file://custom_provider.py` | Custom Python logic |
| HTTP/HTTPS | `id: https://api.example.com/v1/chat` | Generic REST API |
| WebSocket | `id: ws://example.com/ws` | Streaming/real-time API |
| Exec script | `exec: python chain.py` | One-off command |
| MCP | `mcp://...` | Model Context Protocol servers |

## Provider-Specific Test Filtering

Run a test only on certain providers:

```yaml
providers:
  - id: openai:gpt-5-mini
    label: fast-model
  - id: openai:gpt-5.6
    label: smart-model

tests:
  - vars:
      question: 'What is 2+2?'
    providers:
      - fast-model
  - vars:
      question: 'Explain quantum entanglement'
    providers:
      - smart-model
```

Matching supports exact labels, `provider:model`, or wildcards like `openai:*`.

## Model Context Protocol (MCP)

promptfoo supports MCP servers for tool use and agentic capabilities. Configure MCP providers under the provider or target section. See the upstream docs for server-specific setup.

## Next Step

- Custom providers: `phases/07-custom-providers.md`
- Assertions: `phases/06-assertions-metrics.md`
