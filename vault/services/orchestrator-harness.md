# Orchestrator `Harness` (`DevinHarness`) — where it runs, and auth gotchas

## Bottom line

The `devin` CLI subprocess spawned by `DevinHarness.run()` executes **on the
host**, never inside a Docker container. If a skill Activity fails with
`Error: Not logged in. Run devin auth login to authenticate.`, run
`devin auth status` directly in a plain host shell first — it will usually
reproduce the exact same failure, independent of Cadence/the worker/nix-shell.

## Architecture: only Cadence is in Docker

- `docker/docker-compose.yml` runs **only** the Cadence server + Web UI
  (persistence/orchestration engine). See `services/cadence.md`.
- `scripts/start-workflow-engine.sh` starts the `orchestrator.worker` process
  directly on the **host**, backgrounded via `nix-shell --run "... python -m
  orchestrator.worker"` (see its step 3), logging to `scripts/.run/worker.log`.
- That host worker process runs the four skill Activities
  (`src/orchestrator/activities/*.py`). Each goes through
  `skill_activity.run_skill()` -> `Harness.run()` ->
  `DevinHarness.run()` (`src/orchestrator/devin_harness.py`), which does a
  plain `subprocess.run(["devin", "-p", "--permission-mode", ..., "--model",
  ..., "--", prompt], cwd=repo_root)`.
- So the `devin` binary that gets exec'd is whatever is on the **host**
  `PATH` (e.g. `/etc/profiles/per-user/<user>/bin/devin` on this NixOS box) —
  there is no container boundary between the worker and the `devin` CLI call.

## Gotcha: "Not logged in" from the worker is not an env-propagation bug (2026-08-31)

Confirmed by direct reproduction: `devin auth status` fails identically
whether run in a plain interactive shell, inside `nix-shell`, or inspecting
the actual running worker process's `/proc/<pid>/environ` (`HOME`,
`DBUS_SESSION_BUS_ADDRESS`, `XDG_RUNTIME_DIR` were all correctly inherited).
So when this error shows up in a Cadence activity traceback, don't spend time
chasing nix-shell/background-process env stripping first — check CLI auth
directly on the host.

Root cause seen here: `~/.local/share/devin/credentials.toml` contained only
a `windsurf_api_key` session token (auto-populated by the Devin
Desktop/Windsurf IDE integration), not full credentials from a real `devin
auth login`. That session token goes stale, and the standalone `devin` CLI
binary invoked via `subprocess.run` rejects it the same way for every caller
— interactive terminal or background worker alike.

### `devin auth login` refusing to run: "You are already logged in" (2026-08-31)

`devin auth login`'s "already logged in" guard only checks whether
`credentials.toml` *has a token present* — it does **not** validate the
token against the server. `devin auth status` does do a live validation
call, which is why it can say "Not logged in" for the exact same file that
makes `login` refuse to re-authenticate. Net effect: a stale token leaves
you stuck between "status says logged out" and "login says already logged
in" until you break the tie explicitly with `devin auth logout` first.

### Why plain `devin auth logout && devin auth login` wasn't a durable fix

On this box, plain `devin auth login` (browser flow) doesn't do an
independent standalone OAuth login — in this legacy-Windsurf-enterprise
setup (`api_server_url: server.enterprise.windsurf.com`,
`devin_api_url: api.devinenterprise.com`) it re-syncs the credentials file
with the **same underlying Windsurf IDE session token**
(`windsurf_api_key`, tied to a live `windsurf-session-*` id). That
session-bridged token is flaky/short-lived: it validated once right after
login, then went back to "Not logged in" within minutes, independent of
Cadence, the worker, or `nix-shell` (reproduced with a bare `devin auth
status` call in a plain shell). Repeating `logout`/`login` just re-fetches
the same fragile token.

### Confirmed fix: `devin auth login --force-manual-token-flow` (2026-08-31)

The durable fix is to obtain a real, independently-issued API token instead
of relying on the browser-redirect flow that bridges through the live IDE
session:

```bash
devin auth logout
devin auth login --force-manual-token-flow
# follow the prompt: generate a token in the web app, paste it in
```

Per `devin` CLI's own troubleshooting docs, "Devin CLI API tokens do not
expire by default" — this is the documented mechanism for remote/SSH/headless
auth and is what actually resolved this (confirmed working). Plain
`devin auth login` needs a real TTY/browser session and cannot be driven
headlessly/backgrounded (`Error: Login canceled` if you try to background
it) — `--force-manual-token-flow` is also the way to authenticate without a
local browser redirect at all.

Then restart the engine so the worker picks up the fresh credentials:
```bash
scripts/stop-workflow-engine.sh
scripts/start-workflow-engine.sh
```

`scripts/start-workflow-engine.sh` now preflights `devin auth status` before
starting the worker and fails fast with this exact remedy if it's not
authenticated, rather than surfacing as a buried `SkillActivityError` deep
in a Cadence Activity traceback.

## See also

- [Cadence local stack](cadence.md) — what actually runs in Docker.
- [Workflow Engine implementation](../../src/orchestrator/README.md) — `Harness` swapping, layout.
