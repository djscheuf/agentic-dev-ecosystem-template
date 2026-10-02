# Phase 2: Story fidelity

**Goal**: Confirm the *why* and check the change against it. This shifts the review from opinion to intent.

**Comment type**: `story`

## Step A: Assess the requirement itself
- Is the story well-formed: who is it for, what do they need, why does it matter?
- Are the acceptance criteria clear and testable? Are Given/When/Then scenarios present or derivable?
- Is scope explicit: what is in, what is out?
- Ambiguities: record them as comments with a `guidance` question rather than deciding silently.

## Step B: Build a traceability view (internal working table)

| Requirement / criterion | Implementing change (file:lines) | Evidence (test) | Status |
|---|---|---|---|

Status is one of: met, partial, missing, unclear. Carry the "Evidence" column into Phase 3.

## Step C: Judge the gaps
- **Missing criterion**: a stated criterion with no implementing change. Usually `blocking`.
- **Partial implementation**: check the PR description and commits. If the partial scope is an intentional prioritization, do not call it a bug; note it as `comment` or `suggestion` and confirm the follow-up is tracked. If it is unexplained, raise it as a gap.
- **Unrequested change (scope creep)**: changes that trace to no requirement. Ask whether they belong here; they may deserve their own story or PR.
- **Behavior that contradicts intent**: code that works but does not serve the stated need.
- **Emergent stories**: a feature that appeared late (for example during user acceptance testing) still needs its own stated need. Reconstruct it from the user's words and review against that.

## Questions to keep asking
- What user need does this serve, and how would they know it works?
- Does the implementation honor the original intent, or only the literal wording?
- What did the author decide *not* to do, and was that deliberate?
