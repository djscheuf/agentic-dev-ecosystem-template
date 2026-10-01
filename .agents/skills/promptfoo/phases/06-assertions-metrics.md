# Phase 6: Assertions and Metrics

Assertions validate LLM outputs. They are grouped into deterministic (programmatic) and model-assisted (LLM/ML-based) types.

## Using Assertions

Add an `assert` array to a test case:

```yaml
tests:
  - vars:
      question: 'What is 2+2?'
    assert:
      - type: equals
        value: '4'
      - type: contains
        value: 'four'
```

Every assertion can be negated by prepending `not-`:

```yaml
assert:
  - type: not-equals
    value: 'I cannot help with that'
  - type: not-contains
    value: 'error'
```

## Deterministic Assertions

| Type | What it checks |
|------|----------------|
| `equals` | Exact match |
| `contains` / `icontains` | Substring match (case-sensitive / insensitive) |
| `contains-any` / `contains-all` / `icontains-any` / `icontains-all` | Multiple substrings |
| `regex` | Regular expression match |
| `starts-with` | Prefix match |
| `is-json` / `contains-json` | Valid JSON, optionally with schema |
| `is-html` / `contains-html` | HTML presence/validity |
| `is-sql` / `contains-sql` | SQL presence/validity |
| `is-xml` / `contains-xml` | XML presence/validity |
| `is-refusal` / `not-is-refusal` | Refusal detection |
| `javascript` | Custom JS function |
| `python` | Custom Python function |
| `webhook` | External HTTP endpoint |
| `latency` | Response time below threshold (ms) |
| `cost` | Cost below threshold |
| `finish-reason` | Stop reason (stop, length, content_filter, tool_calls) |
| `levenshtein` | Edit distance |
| `rouge-n`, `bleu`, `gleu`, `meteor` | Text similarity metrics |
| `perplexity` / `perplexity-score` | Model confidence (requires logprobs) |
| `trace-span-count`, `trace-span-duration`, `trace-error-spans` | Trace assertions |
| `trajectory:tool-used`, `trajectory:tool-args-match`, `trajectory:tool-sequence`, `trajectory:step-count` | Agent trajectory |
| `skill-used` | Skill usage |
| `classifier` | Classification model |
| `select-best` | Select best output |
| `word-count` | Word count bounds |
| `assert-set` | Group of assertions |

### Examples

```yaml
assert:
  - type: contains-json
    value: file://schema.json

  - type: regex
    value: '\d{4}'

  - type: latency
    threshold: 5000

  - type: cost
    threshold: 0.001

  - type: finish-reason
    value: stop
```

## Model-Assisted Assertions

| Type | Purpose |
|------|---------|
| `llm-rubric` | LLM judges output against a rubric |
| `model-graded-closedqa` | Closed QA evaluation |
| `factuality` | Factual consistency |
| `similar` | Embedding cosine similarity |
| `classifier` | ML classifier |
| `moderation` | Content moderation |
| `g-eval` | G-Eval scoring |
| `answer-relevance` | Relevance of answer to question |
| `context-faithfulness` | Output supported by context (RAG) |
| `context-recall` | Ground truth appears in context |
| `context-relevance` | Context relevant to query |
| `conversation-relevance` | Conversation relevance |
| `trajectory:goal-success` | Agent achieved goal |
| `pi` | Pi Labs preference scoring |
| `max-score` | Max score across graders |

### Example: LLM Rubric

```yaml
assert:
  - type: llm-rubric
    value: Is not apologetic and provides a clear, concise answer
    provider: openai:gpt-5-mini
    threshold: 0.8
```

### Example: Similarity

```yaml
assert:
  - type: similar
    value: 'Hello world'
    threshold: 0.8
    provider: huggingface:sentence-similarity:sentence-transformers/all-MiniLM-L6-v2
```

## Overriding the Grader

Set the LLM used for model-graded assertions at three levels:

1. CLI: `promptfoo eval --grader openai:gpt-5.6`
2. Per-test or suite: `defaultTest.options.provider`
3. Per-assertion: `assertion.provider`

```yaml
defaultTest:
  options:
    provider: openai:gpt-5-mini

# or
tests:
  - assert:
      - type: llm-rubric
        value: Is spoken like a pirate
        provider:
          id: openai:gpt-5.6
          config:
            temperature: 0
```

## Assertion Sets

Require all or a fraction of assertions to pass:

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

## Named Metrics

Tag assertions to aggregate them:

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

## Derived Metrics

Compute composite scores after evaluation:

```yaml
derivedMetrics:
  - name: f1_score
    value: '2 * precision * recall / (precision + recall)'

  - name: avg_tone
    value: 'Tone / __count'
```

`value` can be a mathematical expression or a JavaScript function. Errors are logged at debug level and do not fail the eval.

## CSV Inline Assertions

In CSV/XLSX test files, use `__expected` columns:

```csv
input,__expected
"Hello world","contains: Hello"
"Calculate 5 * 6","equals: 30"
"What's the weather?","llm-rubric: Provides weather information"
```

Multiple assertions use `__expected1`, `__expected2`, etc.

## Next Step

- Custom assertion scripts: `phases/08-evaluation-scripts.md`
