# Phase 3: Configuration Reference

The `promptfooconfig.yaml` file is the central contract. It defines what to evaluate, how to evaluate it, and how to report results.

## Top-Level Config (`TestSuiteConfig` / `UnifiedConfig`)

```yaml
description: Optional human-readable description
tags:
  env: ci
  team: platform

providers: ...        # or targets: ...
prompts: ...
tests: ...
scenarios: ...

defaultTest: ...
outputPath: results.json
sharing: false
writeLatestResults: true

env:
  LOG_LEVEL: debug

derivedMetrics: ...
extensions: ...
metadata: ...
redteam: ...
tracing: ...

commandLineOptions: ...
evaluateOptions: ...
```

## Key Top-Level Properties

| Property | Type | Purpose |
|----------|------|---------|
| `description` | string | Human-readable eval description |
| `tags` | `Record<string,string>` | Run metadata, filterable |
| `providers` / `targets` | string \| object \| array | LLM APIs to test |
| `prompts` | string \| array \| record | Prompts to run |
| `tests` | string \| array \| generator | Test cases |
| `scenarios` | array | Grouped test configurations |
| `defaultTest` | object \| `file://` | Defaults applied to every test |
| `outputPath` | string \| string[] | File(s) to write results |
| `sharing` | boolean \| object | Enable result sharing |
| `writeLatestResults` | boolean | Persist to `promptfoo` storage for web viewer |
| `env` | object | Environment variable overrides |
| `derivedMetrics` | array | Composite metrics |
| `extensions` | string[] | Extension hook files |
| `metadata` | object | Arbitrary config metadata |
| `redteam` | object | Red-team configuration |
| `tracing` | object | OpenTelemetry tracing config |
| `commandLineOptions` | object | Default CLI flags |
| `evaluateOptions` | object | Runtime options (cache, concurrency, etc.) |

## Test Case Properties

Each test case is an object in the `tests` array or generated from a file.

```yaml
tests:
  - description: Optional description
    vars:
      language: French
      input: Hello world
    assert:
      - type: contains
        value: Bonjour
    options:
      provider: openai:gpt-5-mini
      repeat: 2
      transform: output.toUpperCase()
    metadata:
      category: translation
```

| Property | Type | Purpose |
|----------|------|---------|
| `description` | string | Test name, used in UI and filters |
| `vars` | object | Variables substituted into prompts |
| `assert` | array | Assertions for this test |
| `options` | object | Per-test overrides |
| `metadata` | object | Key/value pairs for filtering/reporting |
| `threshold` | number | Minimum pass score (0-1) |
| `providers` | string[] | Limit which providers run this test |

### `options` Object

| Property | Purpose |
|----------|---------|
| `provider` | Provider used for model-graded assertions |
| `transform` | JavaScript/Python transform applied to output before grading |
| `repeat` | Run this test N times |
| `disableDefaultAsserts` | Skip `defaultTest.assert` for this test |
| `response_format` / `temperature` / etc. | Provider-specific overrides |

## `defaultTest`

Apply defaults to all tests:

```yaml
defaultTest:
  vars:
    audience: developer
  assert:
    - type: llm-rubric
      value: Does not describe itself as an AI or chatbot
  options:
    provider: openai:gpt-5-mini
```

Use `options.disableDefaultAsserts: true` on a specific test to override inherited assertions.

## Assertion Properties

```yaml
assert:
  - type: contains
    value: expected text
    threshold: 0.5
    weight: 2
    metric: Tone
    config:
      caseSensitive: false
```

| Property | Purpose |
|----------|---------|
| `type` | Assertion type (required) |
| `value` | Expected value or criteria |
| `threshold` | Score required to pass (varies by type) |
| `weight` | Relative weight in aggregate scoring |
| `metric` | Named metric bucket |
| `provider` | Grader provider for model-graded assertions |
| `rubricPrompt` | Override rubric prompt for model-graded assertions |
| `config` | Assertion-specific config |

## Assertion Sets

Group assertions and require a subset or all to pass:

```yaml
assert:
  - type: assert-set
    threshold: 0.5
    assert:
      - type: cost
        threshold: 0.001
      - type: latency
        threshold: 200
```

## Named and Derived Metrics

Named metrics group assertions:

```yaml
tests:
  - assert:
      - type: equals
        value: Yarr
        metric: Tone
      - type: icontains
        value: grub
        metric: Tone
      - type: is-json
        metric: Consistency
```

Derived metrics compute composite scores:

```yaml
derivedMetrics:
  - name: f1_score
    value: '2 * precision * recall / (precision + recall)'
```

`value` can be a mathematical expression or a JavaScript function. `__count` is available for averages.

## External File Imports

Load any list from a file:

```yaml
prompts:
  - file://prompts/*.txt

providers:
  - file://providers.yaml

tests:
  - file://tests.yaml
  - file://tests.csv

defaultTest: file://default.yaml
```

CSV/XLSX files are auto-mapped from column headers. Use `__expected` columns for inline assertions.

## Multiple Configs

Run multiple configs together:

```bash
promptfoo eval -c config1.yaml -c config2.yaml
promptfoo eval -c my_configs/*
```

## Config Validation

```bash
promptfoo validate config
promptfoo validate target
```

## Next Step

- Prompt formats: `phases/04-prompts.md`
- Provider configuration: `phases/05-providers.md`
