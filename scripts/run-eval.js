#!/usr/bin/env node
/**
 * Runs a promptfoo eval config and prints the resulting eval id as JSON.
 *
 * This is the `test_command` half of the EDD run/inspect identity chain
 * (see ADR-021, ADR-023): `EvaluateCandidateActivity` needs a reliable
 * `evaluation_id` from stdout so it can build an id-scoped `inspect_command`
 * (e.g. `scripts/inspect-eval.js {evaluation_id} --all --json`) instead of
 * falling back to "whatever eval is most recent in evals/".
 *
 * What it reads:
 *   The promptfoo config file named by <config>, resolved relative to the
 *   evals/ directory (same convention as `npm run test`).
 *
 * What it does:
 *   Runs `npx promptfoo eval --no-cache --config <config>` with cwd=evals/.
 *   This is a real evaluation run: it calls the configured provider(s) for
 *   every test case and writes a new eval record to promptfoo's local eval
 *   store (evals/.promptfoo/). It does not modify, move, or delete any
 *   existing files.
 *
 * Output:
 *   promptfoo's own stdout/stderr (the formatted eval table, provider
 *   errors, etc.) is forwarded to this script's stderr, so it stays out of
 *   the JSON channel but is still visible for debugging / artifact capture.
 *   On success this script prints exactly one line of JSON to stdout:
 *     {"evaluation_id": "<eval-id>"}
 *
 * Usage:
 *   scripts/run-eval.js <config.yaml> [...extra promptfoo eval args]
 *   scripts/run-eval.js --dry-run <config.yaml>
 *   scripts/run-eval.js -h | --help
 *
 * Arguments:
 *   <config.yaml>        Path to the promptfoo config, relative to evals/
 *                         (required).
 *   ...extra args         Forwarded verbatim to `promptfoo eval` after
 *                         `--config <config.yaml>`.
 *
 * Options:
 *   --dry-run             Print the promptfoo command that would run and
 *                         exit without invoking promptfoo or writing any
 *                         eval record. Makes no side effects.
 *   -h, --help            Show this help text and exit.
 *
 * Exit code:
 *   - Missing <config.yaml>: exits 1 immediately (no command run), in both
 *     normal and --dry-run mode.
 *   - Normal run: mirrors promptfoo's exit code once an evaluation id has
 *     been captured (per ADR-021, a non-zero exit from failed assertions is
 *     a normal result, not an infra failure).
 *   - If promptfoo runs but no evaluation id can be found in its output,
 *     exits non-zero (promptfoo's exit code, or 1) and prints nothing to
 *     stdout, so the caller can treat it as an evaluation-identity failure.
 *
 * Examples:
 *   scripts/run-eval.js gradeDesign.tests.yaml
 *   scripts/run-eval.js gradeDesign.tests.yaml --filter-pattern "TC-001.*"
 *   scripts/run-eval.js --dry-run gradeDesign.tests.yaml
 */

const { spawnSync } = require('child_process');
const path = require('path');

const REPO_ROOT = path.resolve(__dirname, '..');
const EVALS_DIR = path.join(REPO_ROOT, 'evals');

const STARTING_EVAL_RE = /Starting evaluation (eval-\S+)/;

function printUsageAndExit(code) {
  const usage = require('fs')
    .readFileSync(__filename, 'utf8')
    .split('\n')
    .filter(line => line.startsWith(' *') && line !== ' */')
    .map(line => line.replace(/^\s*\*\s?/, ''))
    .join('\n');
  console.log(usage.trim());
  process.exit(code);
}

function parseArgs(argv) {
  const args = { config: undefined, dryRun: false, extra: [] };
  for (const arg of argv) {
    if (arg === '-h' || arg === '--help') {
      printUsageAndExit(0);
    } else if (arg === '--dry-run') {
      args.dryRun = true;
    } else if (!args.config) {
      args.config = arg;
    } else {
      args.extra.push(arg);
    }
  }
  return args;
}

function main() {
  const args = parseArgs(process.argv.slice(2));

  if (!args.config) {
    console.error('Error: <config.yaml> is required.\n');
    printUsageAndExit(1);
  }

  const promptfooArgs = ['promptfoo', 'eval', '--no-cache', '--config', args.config, ...args.extra];

  if (args.dryRun) {
    console.log('Dry run: no evaluation will be executed and no eval record will be written.');
    console.log(`Would run: npx ${promptfooArgs.join(' ')}`);
    console.log(`  (cwd: ${EVALS_DIR})`);
    process.exit(0);
  }

  const result = spawnSync('npx', promptfooArgs, {
    cwd: EVALS_DIR,
    encoding: 'utf8',
  });

  // Forward promptfoo's own output to our stderr so it stays out of the
  // JSON channel but is still visible to the harness's captured artifacts.
  if (result.stdout) process.stderr.write(result.stdout);
  if (result.stderr) process.stderr.write(result.stderr);

  const combined = `${result.stdout || ''}\n${result.stderr || ''}`;
  const match = combined.match(STARTING_EVAL_RE);
  if (!match) {
    console.error('run-eval.js: could not find an evaluation id in promptfoo output');
    process.exit(result.status && result.status !== 0 ? result.status : 1);
  }

  console.log(JSON.stringify({ evaluation_id: match[1] }));
  // Mirror promptfoo's exit code (ADR-021: a non-zero exit from failed
  // assertions is a normal result, not an infra failure) now that the id
  // has been captured on stdout.
  process.exit(result.status || 0);
}

main();
