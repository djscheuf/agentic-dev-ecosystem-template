# Feedback style

A review is a teaching and trust-building practice first. The reviewer reviews the human behind the code, not only the syntax. Rule one: do no harm (no showing off, no forcing personal style). Rule two: do good (coach through small, explained improvements).

## Two voices, two fields
- **`recommendation`**: direct. State what should change. No hedging, no softening language.
  - "Push the date and user filters into the database query."
- **`guidance`**: coaching. Prefer a question, or the reasoning behind the recommendation, so the author learns to find it next time.
  - "What will the record count be in six months, and how would we notice the endpoint slowing down?"

Keep them distinct. The recommendation says what; the guidance helps the author understand why and how to think about it. If a question adds nothing, leave `guidance` empty.

## Writing each field
- **description**: state what was observed, factually and specifically. Describe the code, not the author. Avoid "you forgot" and "obviously".
- **impact**: explain consequences in terms of users, scale, and future change. This is what justifies the priority.
- **recommendation**: one clear action, with the smallest safe step first when a refactor is large.
- **locations**: precise, verifiable.

## Principles
1. **Explain why.** A change the author understands is one they repeat.
2. **Start with the requirement.** Anchor comments to the story and intent, which moves the conversation from opinion to intent.
3. **Be proportionate.** Match priority to real impact. Flooding a review with `blocking` items, or with trivia, hides the important findings.
4. **Acknowledge what works.** The summary should name real strengths, specifically. Do not invent praise.
5. **Distinguish intent from defect.** When something looks wrong but may be deliberate (a partial implementation, an unusual pattern), ask before calling it a bug.
6. **Adapt to the team.** A technically ideal idiom the team cannot maintain makes the reviewer a bottleneck. Recommend what the team can own, and coach upward.
7. **Do not nitpick what tools can catch.** Leave formatting and style to linters and formatters.
8. **Be honest about uncertainty.** If you could not verify a claim, say so in `impact` or in `limitations`; do not assert it.
9. **Teach the technique.** Where relevant, mention the tool or refactoring step that makes the fix safe (for example, an IDE's extract-method).

## Wording patterns

| Instead of | Prefer |
|---|---|
| "This is wrong." | State the observed gap, then the consequence. |
| "Change this to X." (in `guidance`) | "Have you considered X, given Y?" (in `guidance`); put the direct change in `recommendation`. |
| "Bad naming." | "The name `temp` no longer reflects that this decides whether to flag the invoice; naming it for that decision would help the next reader." |
| "Add tests." | "Add tests for filtering by date and by user, and for the path taken when the audit write fails." |

## General commentary
- Lead with the verdict and the reason.
- Name the main risk and the strongest part of the work.
- Note what you could not check (tests not run, environments unavailable).
- End with the next step, not with a list of everything found.
- Keep it short; the comments carry the detail.

## Verdict phrasing
- `request-changes`: "One item must be fixed before merge: [summary]. The approach is [sound/needs rework]."
- `approve-with-suggestions`: "Sound and aligned with the story. Worth addressing: [summary]."
- `approve`: "Aligned with the story and ready to merge. [optional notes]."
