# Phase 9: CLI Commands and Environment Variables

## Common CLI Options

Most commands support:

- `--env-file, --env-path <path>` — load `.env` files
- `-v, --verbose` — verbose output (note: for `eval`, `-v` is `--vars`; use `--verbose` or `LOG_LEVEL=debug`)
- `--help`

## `promptfoo eval`

Run an evaluation. Reads `promptfooconfig.yaml` by default.

```bash
promptfoo eval
promptfoo eval -c my-config.yaml
```

### Key Flags

| Flag | Purpose |
|------|---------|
| `-c, --config <paths...>` | Config file(s) |
| `-p, --prompts <paths...>` | Override prompts |
| `-r, --providers <names...>` | Override providers |
| `-t, --tests <path>` | Override test file |
| `-a, --assertions <path>` | Override assertions |
| `-o, --output <paths...>` | Output file(s) |
| `-j, --max-concurrency <n>` | Parallelism |
| `--delay <ms>` | Delay between requests |
| `--repeat <n>` | Repeat each test N times |
| `--no-cache` | Disable caching |
| `--no-write` | Do not write latest results |
| `--no-table` | Skip table output |
| `--no-progress-bar` | Quiet progress |
| `-w, --watch` | Watch files and rerun |
| `--resume [evalId]` | Resume a previous eval |
| `--retry-errors` | Retry failed/error cases |
| `--grader <provider>` | Grader for model-graded assertions |
| `--tag <key=value>` | Run metadata tags |
| `--var <key=value>` | Override a single variable |
| `--vars <path>` | Load variables from file |
| `--filter-pattern <regex>` | Filter tests by description |
| `--filter-providers <pattern>` | Filter providers |
| `--filter-prompts <pattern>` | Filter prompts |
| `--filter-metadata <key=value>` | Filter tests by metadata |
| `--filter-range <start:end>` | Run a stable index slice |
| `--filter-sample <n>` | Random sample of N tests |
| `--filter-sample-seed <n>` | Seed for random sample |
| `--filter-failing <path>` | Re-run tests that failed in a previous eval |
| `--filter-errors-only <path>` | Re-run only errors |
| `--suggest-prompts <n>` | Generate prompt suggestions |

### Exit Codes

- `0` — all tests passed
- `100` — at least one failure or pass rate below `PROMPTFOO_PASS_RATE_THRESHOLD`
- `1` — any other error
- Override failed-test exit code with `PROMPTFOO_FAILED_TEST_EXIT_CODE`

## `promptfoo view`

Start the interactive web UI:

```bash
promptfoo view
promptfoo view -p 3000
```

If you changed `PROMPTFOO_CONFIG_DIR`, pass the directory:

```bash
promptfoo view /path/to/config-dir
```

## `promptfoo optimize`

Improve one prompt against one provider:

```bash
promptfoo optimize
promptfoo optimize -c path/to/config.yaml --prompt-index 1 --provider-index 0
promptfoo optimize --validation-split 0.2
```

Without `--validation-split`, optimization may overfit to the configured test set.

## `promptfoo validate`

```bash
promptfoo validate config
promptfoo validate target
```

## `promptfoo init`

Create a new project or example:

```bash
promptfoo init
promptfoo init my-project --example getting-started
```

## `promptfoo generate dataset`

Generate synthetic test cases:

```bash
promptfoo generate dataset -w
promptfoo generate dataset -c my_config.yaml -o new_tests.yaml -i 'European cities only'
```

## `promptfoo generate assertions`

Generate additional assertions:

```bash
promptfoo generate assertions -w
promptfoo generate assertions -c my_config.yaml -o new_asserts.yaml -i 'pronunciation checks'
```

## `promptfoo cache`

```bash
promptfoo cache clear
```

## `promptfoo logs`

```bash
promptfoo logs --list
promptfoo logs <filename>
```

## `promptfoo debug`

Display debug information for troubleshooting:

```bash
promptfoo debug -c my-config.yaml
```

## `promptfoo share [id]`

Create a shareable URL for the most recent eval or a specific ID.

## `promptfoo list`

```bash
promptfoo list evals
promptfoo list prompts
promptfoo list datasets
```

## `promptfoo export`

```bash
promptfoo export eval <evalId>
promptfoo export logs
```

## Environment Variables

promptfoo reads `.env` from the working directory.

### General

| Variable | Purpose | Default |
|----------|---------|---------|
| `PROMPTFOO_CACHE_ENABLED` | Enable cache | `true` |
| `PROMPTFOO_CACHE_TYPE` | `disk` or `memory` | `disk` |
| `PROMPTFOO_CACHE_PATH` | Cache directory | `~/.promptfoo/cache` |
| `PROMPTFOO_CACHE_TTL` | Cache TTL seconds | `1209600` |
| `PROMPTFOO_CONFIG_DIR` | Config/data directory | `~/.promptfoo` |
| `PROMPTFOO_LOG_DIR` | Log directory | `~/.promptfoo/logs` |
| `PROMPTFOO_EVAL_TIMEOUT_MS` | Per-request timeout | — |
| `PROMPTFOO_MAX_EVAL_TIME_MS` | Total eval timeout | — |
| `PROMPTFOO_PASS_RATE_THRESHOLD` | Minimum pass rate | — |
| `PROMPTFOO_FAILED_TEST_EXIT_CODE` | Override exit code 100 | — |
| `PROMPTFOO_MAX_EVAL_TIME_MS` | Total eval time limit | — |
| `PROMPTFOO_REQUIRE_JSON_PROMPTS` | Require JSON prompts | `false` |
| `PROMPTFOO_DISABLE_UPDATE` | Disable update checks | `false` |
| `PROMPTFOO_DISABLE_RUNTIME_WARNINGS` | Disable runtime warnings | `false` |
| `PROMPTFOO_DISABLE_REMOTE_GENERATION` | Disable remote generation | `false` |
| `PROMPTFOO_DISABLE_TEMPLATING` | Disable Nunjucks | `false` |
| `PROMPTFOO_DISABLE_VAR_EXPANSION` | Disable var expansion | `false` |
| `PROMPTFOO_DISABLE_JSON_AUTOESCAPE` | Disable JSON escaping | `false` |
| `PROMPTFOO_DISABLE_OBJECT_STRINGIFY` | Disable object stringify | `false` |
| `PROMPTFOO_DISABLE_ERROR_LOG` | Disable error log | `false` |
| `PROMPTFOO_DISABLE_DEBUG_LOG` | Disable debug log | `false` |

### Memory/Output Stripping

| Variable | Purpose |
|----------|---------|
| `PROMPTFOO_STRIP_PROMPT_TEXT` | Strip prompt text from outputs |
| `PROMPTFOO_STRIP_RESPONSE_OUTPUT` | Strip model outputs |
| `PROMPTFOO_STRIP_TEST_VARS` | Strip test variables |
| `PROMPTFOO_STRIP_GRADING_RESULT` | Strip grading results |
| `PROMPTFOO_STRIP_METADATA` | Strip metadata |

### Python Integration

| Variable | Purpose |
|----------|---------|
| `PROMPTFOO_PYTHON` | Path to Python executable |
| `PROMPTFOO_PYTHON_DEBUG_ENABLED` | Enable `pdb` debugging |

### Provider-Specific

| Variable | Provider |
|----------|----------|
| `OPENAI_API_KEY` | OpenAI |
| `OPENAI_BASE_URL` | OpenAI custom endpoint |
| `ANTHROPIC_API_KEY` | Anthropic |
| `OLLAMA_BASE_URL` | Ollama |
| `OLLAMA_API_KEY` | Ollama |
| `REQUEST_TIMEOUT_MS` | Ollama |
| `WITHPI_API_KEY` | Pi scorer |

## Command-Line Options in Config

Set defaults in `promptfooconfig.yaml`:

```yaml
commandLineOptions:
  maxConcurrency: 10
  repeat: 3
  delay: 1000
  verbose: true
  grader: openai:gpt-5-mini
  cache: false
  filterPattern: 'auth.*'
  var:
    temperature: '0.7'
```

CLI flags override these defaults.

## Next Step

- Debugging: `phases/10-debugging-scenarios.md`
