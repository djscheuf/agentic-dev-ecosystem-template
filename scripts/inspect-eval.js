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
 *   --prompt-chars <n>   Max characters of rendered prompt to print for failing results (default: 4000)
 *   --json               Print the filtered results as raw JSON instead of a formatted summary
 *   --compact-json       Print a compact agent-friendly JSON summary: top-level pass/fail totals
 *                        (passing/failing/total/percentage) plus a trimmed tests array for *all*
 *                        test cases. Passing cases include only identification fields; failing
 *                        cases include prompt, vars, output, and failed assertion details.
 *   --coverage-metadata-property <path>
 *                        Dotted path to a metadata field (e.g. metadata.covers_test_case_ids)
 *                        that should be aggregated from all tests and mirrored at the top level
 *                        of a --compact-json output. This keeps the compact format compatible
 *                        with downstream coverage calculators.
 *   -h, --help           Show this help text
 *
 * Examples:
 *   scripts/inspect-eval.js
 *   scripts/inspect-eval.js eval-wtL-2026-09-11T01:25:00
 *   scripts/inspect-eval.js --all --output-chars 300
 *   scripts/inspect-eval.js eval-wtL-2026-09-11T01:25:00 --compact-json
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
  const args = {
    evalId: undefined,
    all: false,
    outputChars: 1200,
    promptChars: 4000,
    json: false,
    compactJson: false,
    coverageMetadataProperty: undefined,
  };
  for (let i = 0; i < argv.length; i++) {
    const arg = argv[i];
    if (arg === '-h' || arg === '--help') {
      printUsageAndExit(0);
    } else if (arg === '--all') {
      args.all = true;
    } else if (arg === '--json') {
      args.json = true;
    } else if (arg === '--compact-json') {
      args.compactJson = true;
    } else if (arg.startsWith('--output-chars=')) {
      args.outputChars = Number(arg.split('=')[1]);
    } else if (arg === '--output-chars') {
      args.outputChars = Number(argv[++i]);
    } else if (arg.startsWith('--prompt-chars=')) {
      args.promptChars = Number(arg.split('=')[1]);
    } else if (arg === '--prompt-chars') {
      args.promptChars = Number(argv[++i]);
    } else if (arg.startsWith('--coverage-metadata-property=')) {
      args.coverageMetadataProperty = arg.split('=').slice(1).join('=');
    } else if (arg === '--coverage-metadata-property') {
      args.coverageMetadataProperty = argv[++i];
    } else if (!arg.startsWith('-') && !args.evalId) {
      args.evalId = arg;
    } else {
      console.error(`Unknown argument: ${arg}`);
      printUsageAndExit(1);
    }
  }
  return args;
}

function getPath(obj, path) {
  const parts = path.split('.');
  let value = obj;
  for (const part of parts) {
    if (value == null || typeof value !== 'object') return undefined;
    value = value[part];
  }
  return value;
}

function setPath(obj, path, value) {
  const parts = path.split('.');
  let target = obj;
  for (let i = 0; i < parts.length - 1; i++) {
    const part = parts[i];
    if (target[part] == null || typeof target[part] !== 'object') {
      target[part] = {};
    }
    target = target[part];
  }
  target[parts[parts.length - 1]] = value;
}

function collectCoverageMetadata(results, propertyPath) {
  const collected = new Set();
  for (const r of results) {
    const value = getPath(r.testCase, propertyPath);
    if (Array.isArray(value)) {
      for (const item of value) collected.add(String(item));
    } else if (value != null) {
      collected.add(String(value));
    }
  }
  return Array.from(collected);
}

function truncate(str, maxChars) {
  if (typeof str !== 'string') return str;
  if (maxChars <= 0 || str.length <= maxChars) return str;
  return str.slice(0, maxChars) + `\n... [truncated: ${str.length - maxChars} more chars]`;
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

function buildCompactJson(evalData, { outputChars, promptChars, coverageMetadataProperty }) {
  const results = evalData.results?.results || evalData.results || [];
  const total = results.length;
  const passing = results.filter(r => r.success === true && !r.error).length;
  const failing = total - passing;
  const percentage = total > 0 ? (passing / total) * 100 : 0.0;

  const compact = {
    passing,
    failing,
    total,
    percentage: Number(percentage.toFixed(2)),
    tests: [],
  };

  if (coverageMetadataProperty) {
    const coverageValues = collectCoverageMetadata(results, coverageMetadataProperty);
    setPath(compact, coverageMetadataProperty, coverageValues);
  }

  compact.tests = results.map((r, idx) => {
    const status = r.error ? 'error' : r.success === false ? 'fail' : 'pass';
    const base = {
      index: idx,
      testIdx: r.testIdx,
      promptIdx: r.promptIdx,
      description: r.testCase?.description || '(no description)',
      status,
      provider: r.provider?.label || r.provider?.id || 'unknown provider',
      metadata: r.testCase?.metadata || undefined,
    };

    // Passing tests need only enough context to identify them.
    if (status === 'pass') {
      return base;
    }

    // For failures and errors, include the details an agent needs to diagnose.
    const detail = {
      ...base,
      vars: r.testCase?.vars || r.vars || undefined,
      prompt: truncate(r.prompt?.raw || r.prompt, promptChars),
      output: truncate(r.response?.output, outputChars),
      error: r.error || undefined,
    };

    if (r.gradingResult) {
      const componentResults = (r.gradingResult.componentResults || []).filter(c => !c.pass);
      detail.gradingResult = {
        pass: r.gradingResult.pass,
        score: r.gradingResult.score,
        reason: r.gradingResult.reason,
        componentResults: componentResults.length > 0 ? componentResults : undefined,
      };
    }

    return detail;
  });

  return compact;
}

function summarize(evalData, { all, outputChars, promptChars, json, compactJson, coverageMetadataProperty }) {
  const results = evalData.results?.results || evalData.results || [];
  const filtered = all ? results : results.filter(r => r.success === false);

  if (compactJson) {
    const compact = buildCompactJson(evalData, { outputChars, promptChars, coverageMetadataProperty });
    console.log(JSON.stringify(compact, null, 2));
    return { total: results.length, shown: compact.tests.length };
  }

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
  if (!args.json && !args.compactJson) {
    console.log(`\n${'='.repeat(80)}`);
    console.log(`Showing ${shown}/${total} results${args.all ? '' : ' (failures/errors only; pass --all to see everything)'}`);
  } else if (args.json) {
    console.error(`Showing ${shown}/${total} results${args.all ? '' : ' (failures/errors only; pass --all to see everything)'}`);
  } else {
    console.error(`Showing ${shown}/${total} test summaries`);
  }
}

main();
