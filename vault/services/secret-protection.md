# Secret Protection

Reads of environment files that may contain secrets are blocked by a `PreToolUse` hook.
Use `.envrc.example` as the safe reference for what variables are available.

## Blocked env files

The hook `.devin/scripts/protect-secrets.sh` runs on every `read` tool call.
It blocks files whose basename matches:

- `.env`
- `.envrc`
- `.env.local`, `.envrc.local`
- `.env.*.local`, `.envrc.*.local`
- `.env.*`, `.envrc.*`

Absolute paths are resolved to their basename, so `/path/to/.envrc` is also blocked.

## Safe reference

`.envrc.example` is intentionally allowed.
It lists the environment variables the project uses, without real secret values.

## Hook wiring

`/.devin/hooks.json` registers the hook for every `read`:

```json
{
  "PreToolUse": [
    {
      "matcher": "read",
      "hooks": [
        {
          "type": "command",
          "command": "bash .devin/scripts/protect-secrets.sh"
        }
      ]
    }
  ]
}
```

When an env file is read, the hook exits `2` (block) and prints a message pointing to `.envrc.example`.

## Last updated

2026-09-24
