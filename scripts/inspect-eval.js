#!/usr/bin/env node
/**
 * Reusable util for extracting and reading a promptfoo eval result.
 *
 * Wraps `promptfoo export eval <id>` (run from evals/, where node_modules/promptfoo lives)
 * and prints a concise summary instead of the truncated CLI table, so failures/errors can be
 * diagnosed directly from raw provider output and assertion reasons.
 *
 * Usage:
 *   scripts/inspect-eval.js [evalId] [options]
 *
 * Arguments:
 *   evalId              Eval ID to inspect (e.g. eval-abc-2026-01-01T00:00:00). Defaults to the
 *                        most recent eval if omitted.
 *
 * Options:
 *   --all                Show passing results too (default: failures/errors only)
 *   --output-chars <n>   Max characters of raw provider output to print per result (default: 1200)
 *   --json               Print the filtered results as raw JSON instead of a formatted summary
 *   -h, --help           Show this help text
 *
 * Examples:
 *   scripts/inspect-eval.js
 *   scripts/inspect-eval.js eval-wtL-2026-09-11T01:25:00
 *   scripts/inspect-eval.js --all --output-chars 300
 */

const { execFileSync } = require('child_process');
const fs = require('fs');
const os = require('os');
const path = require('path');

const REPO_ROOT = path.resolve(__dirname, '..');
const EVALS_DIR = path.join(REPO_ROOT, 'evals');

function printUsageAndExit(code) {
  const usage = fs
    .readFileSync(__filename, 'utf8')
    .split('\n')
    .filter(line => line.startsWith(' *') && line !== ' */')
    .map(line => line.replace(/^\s*\*\s?/, ''))
    .join('\n');
  console.log(usage.trim());
  process.exit(code);
}

function parseArgs(argv) {
  const args = { evalId: undefined, all: false, outputChars: 1200, json: false };
  for (const arg of argv) {
    if (arg === '-h' || arg === '--help') {
      printUsageAndExit(0);
    } else if (arg === '--all') {
      args.all = true;
    } else if (arg === '--json') {
      args.json = true;
    } else if (arg.startsWith('--output-chars=')) {
      args.outputChars = Number(arg.split('=')[1]);
    } else if (arg === '--output-chars') {
      // handled by the value that follows; see loop below
      args._expectOutputChars = true;
    } else if (args._expectOutputChars) {
      args.outputChars = Number(arg);
      args._expectOutputChars = false;
    } else if (!arg.startsWith('-') && !args.evalId) {
      args.evalId = arg;
    } else {
      console.error(`Unknown argument: ${arg}`);
      printUsageAndExit(1);
    }
  }
  delete args._expectOutputChars;
  return args;
}

function resolveLatestEvalId() {
  const listOutput = execFileSync('npx', ['promptfoo', 'list', 'evals'], {
    cwd: EVALS_DIR,
    encoding: 'utf8',
  });
  // `promptfoo list evals` prints oldest-first, so the last match is the most recent eval.
  const matches = listOutput.match(/eval-[A-Za-z0-9]+-\d{4}-\d{2}-\d{2}T[\d:]+/g);
  if (!matches || matches.length === 0) {
    throw new Error('Could not find any eval IDs via `promptfoo list evals`.');
  }
  return matches[matches.length - 1];
}

function exportEval(evalId) {
  const tmpFile = path.join(os.tmpdir(), `inspect-eval-${evalId}.json`);
  execFileSync('npx', ['promptfoo', 'export', 'eval', evalId, '-o', tmpFile], {
    cwd: EVALS_DIR,
    encoding: 'utf8',
  });
  return JSON.parse(fs.readFileSync(tmpFile, 'utf8'));
}

function summarize(evalData, { all, outputChars, json }) {
  const results = evalData.results?.results || evalData.results || [];
  const filtered = all ? results : results.filter(r => r.success === false);

  if (json) {
    console.log(JSON.stringify(filtered, null, 2));
    return { total: results.length, shown: filtered.length };
  }

  filtered.forEach((r, idx) => {
    const status = r.error ? 'ERROR' : r.success === false ? 'FAIL' : 'PASS';
    console.log(`\n${'='.repeat(80)}`);
    console.log(`#${idx + 1} [${status}] ${r.testCase?.description || '(no description)'} | provider: ${r.provider?.label || r.provider?.id}`);
    if (r.testCase?.vars && Object.keys(r.testCase.vars).length > 0) {
      console.log(`vars: ${JSON.stringify(r.testCase.vars).slice(0, 300)}`);
    }
    if (r.error) {
      console.log(`error: ${r.error}`);
    }
    const failedAsserts = (r.gradingResult?.componentResults || []).filter(c => !c.pass);
    failedAsserts.forEach(fa => {
      console.log(`  FAILED[${fa.assertion?.metric || fa.assertion?.type}]: ${fa.reason}`);
    });
    const output = r.response?.output;
    if (output) {
      const snippet = outputChars > 0 ? output.slice(0, outputChars) : output;
      console.log(`--- raw output (${output.length} chars${outputChars > 0 && output.length > outputChars ? `, truncated to ${outputChars}` : ''}) ---`);
      console.log(snippet);
    }
  });

  return { total: results.length, shown: filtered.length };
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  const evalId = args.evalId || resolveLatestEvalId();
  console.error(`Inspecting eval: ${evalId}`);
  const evalData = exportEval(evalId);
  const { total, shown } = summarize(evalData, args);
  if (!args.json) {
    console.log(`\n${'='.repeat(80)}`);
    console.log(`Showing ${shown}/${total} results${args.all ? '' : ' (failures/errors only; pass --all to see everything)'}`);
  } else {
    console.error(`Showing ${shown}/${total} results${args.all ? '' : ' (failures/errors only; pass --all to see everything)'}`);
  }
}

main();
