# grade-story-design Evaluation Suite Refinement Process

Iterative refinement of the `grade-story-design` promptfoo eval suite follows a startup → plan → do → check → adjust loop. Agentic steps require judgment; deterministic steps can be scripted or validated automatically. The live evaluation command must be run in an authenticated Devin CLI environment and cannot be exercised from an unauthenticated sandbox.

See also:
- [[decisions/ADR-017-agentic-edd-quality-ratchet.md]] — when to accept, rerun, reject, or stop a candidate.
- [[decisions/ADR-019-edd-multi-iteration-loop.md]] — workflow-level loop mechanics.
- [[decisions/ADR-021-edd-evaluation-command-contracts.md]] — non-zero exits and inspect-command parsing.
- `docs/reqs/refine-grade-design/` — the specific refinement requirements that drive this session.

## Startup: load context

**Type:** mixed (deterministic reads + agentic synthesis)

**Inputs:**
- The top-level eval config: `evals/gradeDesign.tests.yaml`
- The required test-case catalog: `.devin/skills/grade-story-design/_tests/test-cases.yaml`
- The rubric the skill is graded against (in the skill's prompt or `SKILL.md`)
- The grading helper: `.devin/skills/grade-story-design/_tests/gradeDesignChecks.js`
- Existing fixtures under `.devin/skills/grade-story-design/_tests/_data/`
- Any recent evaluation artifacts or prior run summaries the user shares

**Outputs:**
- A coverage map: which required test case is exercised by which YAML assertion, and at what expected score
- A gap list: required test cases with no deterministic coverage

**Implicit rules:**
- Treat `hasExpectedFailingSections` assertions carefully: `score_floor` is a *floor*, not necessarily the *exact* expected score, unless `assert_config.exact: true` is present.
- Read the helper script before assuming assertion semantics; helper bugs (e.g. falsy handling of `0`) are a common source of misclassified gaps.
- Map to the *required* test-case IDs, not just the assertion descriptions, so coverage is auditable.

## Plan: scope the next refinement

**Type:** agentic

**Inputs:**
- Gap list from startup
- Fixture inventory (which fixtures are "good", "truncated", "stripped", etc.)
- Time/budget constraints and the user's chosen tier (e.g. Tier 1 quick wins)

**Outputs:**
- A tiered plan, typically:
  - **Tier 1:** no new fixtures needed; tighten existing assertions; add exemplary (score=3) tests using rich existing fixtures.
  - **Tier 2:** second "minimal" flavor per dimension; may need to tweak or lightly adapt existing fixtures.
  - **Tier 3:** "adequate" (score=2) tests; usually requires new fixtures that model "good but imperfect" designs.
- A decision on assertion strictness: exact-score checks vs. floor checks, and whether `llm-rubric` assertions should look for specific phrasing or absence-of-gap.

**Implicit rules:**
- Prefer quick wins that increase required-test-case coverage before building new fixtures.
- Add exact-score assertions only when the fixture genuinely supports a single unambiguous score; otherwise keep a floor and add `llm-rubric` guardrails.
- Do not plan to change evaluation expectations (what score a fixture "should" get) without explicit human approval; changing expectations is a separate EDD approval gate.

## Do: edit tests, fixtures, and helpers

**Type:** mixed (agentic choices, deterministic edits)

**Inputs:**
- The planned changes
- Existing YAML, JSON fixtures, and helper JS

**Outputs:**
- Modified YAML test cases
- Modified or new fixtures
- Modified helper code (e.g. fixing `||` to `??` for falsy numeric values)

**Implicit rules:**
- Follow existing YAML structure and naming conventions; copy an existing test block and modify only what changes.
- When adding a fixture, ensure internal consistency across all design sections (`questions_addressed`, `workflow_sequence`, `contracts`, `layer_responsibilities`, `instrumentation`). A contradiction caught by the grader is a fixture bug, not a flaky model.
- Use the existing fixture naming convention: `<story>.design.json`.
- Prefer adding `exact: true` to `assert_config` over rewriting the helper's default semantics, so existing tests keep their old behavior.

## Check: validate and run

**Type:** mixed

### Deterministic pre-run checks

Run after every batch of edits:

```bash
# YAML syntax check for all test-suite files
node -e "
const yaml = require('js-yaml');
const fs = require('fs');
[
  '.devin/skills/grade-story-design/_tests/incomplete-design.tests.yaml',
  '.devin/skills/grade-story-design/_tests/interface-contracts.tests.yaml',
  '.devin/skills/grade-story-design/_tests/layer-responsibilities.tests.yaml',
  '.devin/skills/grade-story-design/_tests/instrumentation-observability.tests.yaml'
].forEach(f => { yaml.load(fs.readFileSync(f, 'utf8')); console.log(f, 'OK'); });
"

# JSON fixture validity
python3 -c "import json; json.load(open('.devin/skills/grade-story-design/_tests/_data/admin-tactic-types.design.json')); print('JSON OK')"

# Helper unit-level sanity checks (e.g. score_floor: 0 is not coerced to undefined)
node -e "<quick inline test of _pullVarFromAssertConfig>"
```

**Inputs:** edited files
**Outputs:** pass/fail for syntax and basic logic

### Live evaluation run

```bash
node scripts/run-eval.js gradeDesign.tests.yaml
```

**Type:** deterministic command, **but requires authenticated Devin CLI**

**Inputs:** the full eval config, provider credentials, the current skill prompt
**Outputs:** a promptfoo evaluation result set (pass/fail per assertion, per-test scores, logs)

**Sandbox limitation:** This command cannot be run from an unauthenticated Devin Desktop sandbox because it invokes `devin` CLI commands that require a logged-in session. The agent must ask the user to run it in an authenticated terminal and share the results, or rely on the EDD workflow harness to run it.

### Inspect results

If deep inspection is needed, use:

```bash
node scripts/inspect-eval.js --all --json
node scripts/inspect-eval.js eval-<id> --all --json
```

**Inputs:** latest evaluation id or auto-detected latest run
**Outputs:** raw per-result objects used to compute pass/fail/coverage metrics

**Implicit rules:**
- A non-zero exit from `node scripts/run-eval.js` is a normal signal of failing assertions, not an infrastructure crash, per [[decisions/ADR-021-edd-evaluation-command-contracts.md]].
- Distinguish helper errors (e.g. "Missing Assert Config") from assertion failures; helper errors usually indicate a bug in `gradeDesignChecks.js`, not a bad model output.

## Adjust: classify failures and fix the right layer

**Type:** agentic

**Inputs:**
- Failing assertion output
- Fixture content
- Rubric language for the dimension in question

**Outputs:**
- A classification for each failure:
  - **Fixture bug:** the design document is internally inconsistent or contradicts its own `questions_addressed`/`workflow_sequence`; fix the fixture.
  - **Assertion brittleness:** the test expects wording the grader didn't use even though the substance is correct; relax the `llm-rubric` or exact-score check.
  - **Helper bug:** the assertion runner misreads `assert_config` (e.g. `score_floor: 0` treated as missing); fix the helper.
  - **Real model gap:** the grader genuinely mis-scored a fixture; may need prompt improvement or an approved expectation change.
  - **Coverage gap:** no fixture or assertion covers the required test case; add it in the next plan cycle.

**Implicit rules:**
- Always fix fixture contradictions before relaxing assertions; otherwise the test suite learns to accept bad reasoning.
- For `llm-rubric` assertions, prefer checking for the *absence of a named concrete gap* over requiring specific praise like "no recommendation needed."
- For exact-score assertions, make sure the fixture has no other plausible interpretation; exemplary fixtures often need to be richer and more internally consistent than "good enough" fixtures.
- If the same failure appears across multiple runs unchanged, treat it as a deterministic issue, not LLM noise.

## Repeat

Return to **Check** after each adjustment. The loop continues until:
- all deterministic pre-run checks pass,
- the live evaluation run passes at the current tier,
- the required-test-case coverage meets the planned goal, or
- the user or the quality ratchet decides to stop.

Per [[decisions/ADR-017-agentic-edd-quality-ratchet.md]]: compare each candidate against the current best accepted state, confirm apparent regressions with a rerun, and stop after three consecutive confirmed harmful proposals.

## Deterministic vs. agentic step summary

| Step | Type | Why |
|---|---|---|
| Load context | mixed | reads are deterministic; synthesizing a gap map requires judgment |
| Coverage mapping | agentic | deciding what a test "covers" depends on intent and rubric interpretation |
| Prioritization / tier planning | agentic | trade-off between coverage, cost, and fixture effort |
| Editing YAML/JSON/JS | mixed | mechanics are deterministic, but what to change is agentic |
| YAML/JSON/JS syntax validation | deterministic | can be fully scripted |
| Helper logic sanity checks | deterministic | inline assertions or small unit tests |
| Live `node scripts/run-eval.js` | deterministic command | same inputs should produce same outputs, but needs external auth |
| Inspect raw results | deterministic | parses structured output |
| Classify failures | agentic | requires distinguishing fixture bug, brittleness, helper bug, real gap |
| Decide next adjustment | agentic | chooses which layer to fix and how |
| Loop control | agentic | applies the quality-ratchet stopping rules |

## Session-specific artifacts to preserve

When this process is run manually or through the EDD workflow, keep:
- the initial gap map,
- the tier plan accepted by the user,
- each edited file's diff,
- deterministic validation output,
- live evaluation results per run,
- the failure classification log and the rationale for each fix,
- the final accepted state and its required-test-case coverage count.
