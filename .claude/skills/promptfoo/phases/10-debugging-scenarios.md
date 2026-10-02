# Phase 10: Debugging and Troubleshooting

## Log Files and Debugging

Default log directory: `~/.promptfoo/logs`

- View from CLI: `promptfoo logs --list` and `promptfoo logs <filename>`
- Custom directory: `PROMPTFOO_LOG_DIR=./logs promptfoo eval`
- Export logs: `promptfoo export logs`
- Enable debug logs: `LOG_LEVEL=debug npx promptfoo eval` or `npx promptfoo eval --verbose`
- Live debug toggle: `promptfoo eval` with verbose mode to see real-time details

## Scenario: Out of Memory

For large evals, reduce memory pressure:

```bash
# Required: do not use --no-write
# Avoid table rendering
promptfoo eval --no-table --output results.jsonl
```

Strip heavy data:

```bash
export PROMPTFOO_STRIP_PROMPT_TEXT=true
export PROMPTFOO_STRIP_RESPONSE_OUTPUT=true
export PROMPTFOO_STRIP_TEST_VARS=true
export PROMPTFOO_STRIP_GRADING_RESULT=true
export PROMPTFOO_STRIP_METADATA=true
```

Increase Node.js heap:

```bash
NODE_OPTIONS="--max-old-space-size=8192" npx promptfoo eval
```

## Scenario: Stuck or Slow Evals

Set timeouts:

```bash
export PROMPTFOO_EVAL_TIMEOUT_MS=30000      # per request
export PROMPTFOO_MAX_EVAL_TIME_MS=300000    # total eval
```

Or in config:

```yaml
env:
  PROMPTFOO_EVAL_TIMEOUT_MS: 30000
  PROMPTFOO_MAX_EVAL_TIME_MS: 300000
```

Reduce concurrency for rate-limited providers:

```bash
promptfoo eval -j 1 --delay 1000
```

Disable cache only when fresh calls are required:

```bash
promptfoo eval --no-cache
```

## Scenario: Custom Python Provider Not Found

Symptoms: `spawn py -3 ENOENT` or `Python 3 not found`

Fixes:

1. Set the Python path:

   ```bash
   export PROMPTFOO_PYTHON=/usr/local/bin/python3
   ```

2. Or set per-provider:

   ```yaml
   providers:
     - id: 'file://my_provider.py'
       config:
         pythonExecutable: /path/to/python
   ```

3. Test that Python is reachable:

   ```bash
   python -c "import sys; print(sys.executable)"
   ```

## Scenario: Debugging Python Providers/Assertions

Enable debug output:

```bash
LOG_LEVEL=debug npx promptfoo eval
```

Use `pdb`:

```bash
export PROMPTFOO_PYTHON_DEBUG_ENABLED=true
```

Add breakpoints in your Python code:

```python
import pdb

def call_api(prompt, options, context):
    pdb.set_trace()
    # ...
```

## Scenario: Custom JavaScript Provider Not Loading

- Ensure the file exports a default class or function
- Check that the path is correct relative to the config file
- Use `LOG_LEVEL=debug` to see load errors
- Verify Node.js version is `^20.20.0` or `>=22.22.0`

## Scenario: Provider Authentication Errors

- Confirm the relevant API key env var is set
- For inline keys, verify the provider `config.apiKey` value
- Check `apiBaseUrl` / `apiHost` if using a proxy or custom endpoint
- Use `promptfoo debug -c config.yaml` to inspect resolved config

## Scenario: Object Template Handling

If you see `[object Object]` in prompts or outputs, you are passing an object variable without property access or a filter.

Fix:

```yaml
# Instead of {{user}}
# Use {{user.name}} or {{user | json}}
```

## Scenario: Network / Proxy Issues

Configure proxy:

```bash
export HTTP_PROXY=http://proxy.example.com:8080
export HTTPS_PROXY=http://proxy.example.com:8080
```

Custom CA certificates:

```bash
export NODE_EXTRA_CA_CERTS=/path/to/cert.pem
```

## Scenario: Ollama Connection Refused

Common causes:

- Ollama not listening on `0.0.0.0` for remote connections
- IPv4/IPv6 mismatch with `localhost`

Fixes:

```bash
# Use explicit IPv4
export OLLAMA_BASE_URL=http://127.0.0.1:11434

# Or start Ollama on all interfaces
export OLLAMA_HOST=0.0.0.0:11434
ollama serve
```

## Scenario: Assertion Failures Are Hard to Understand

- Use `promptfoo view` to inspect the actual prompt, output, and assertion result
- Return full `GradingResult` objects from custom assertions with a `reason` field
- Add `description` fields to test cases for easier filtering

## Scenario: Caching Surprises Results

- `--no-cache` ensures fresh calls
- `--repeat` uses separate cache entries; add `--no-cache` if every repeat must call the provider
- Clear cache: `promptfoo cache clear`

## Scenario: Runtime Warnings / Update Checks

Disable if needed:

```bash
export PROMPTFOO_DISABLE_RUNTIME_WARNINGS=true
export PROMPTFOO_DISABLE_UPDATE=true
```

## Validation Before Debugging

Run config validation before a full eval:

```bash
promptfoo validate config
promptfoo validate target
```

## Debugging Checklist

1. Check logs at `~/.promptfoo/logs` or `PROMPTFOO_LOG_DIR`
2. Run with `LOG_LEVEL=debug` or `--verbose`
3. Validate config with `promptfoo validate config`
4. Isolate the failing test with `--filter-pattern` or `--filter-range`
5. Test the provider directly (custom providers can be unit-tested independently)
6. Disable cache if stale results are suspected
7. Check timeouts and concurrency for stuck evals
8. Inspect output stripping options for OOM

## Next Step

- Quick reference: `quick-reference.md`
