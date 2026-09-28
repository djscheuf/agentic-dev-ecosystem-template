---
name: grade-story-design
description: Grades the quality of the design document for a given story with additional details based on the Design Quality Rubric
---

## Steps:
### 1. Read the Analysis JSON
- Read the analysis json document.

### 2. Grade the Design
- grade the design based on the Implementation Design Quality Rubric defined in `/rubric.md`.
- Identify a score for each dimension and provide your reasoning for that score. 
- Provide recommendations for improvement for each dimension with an imperfect score.
- Before scoring, tally the evidence per dimension (e.g. count how many decisions/steps/contracts are grounded vs. weak) — this tally drives the score even if it isn't fully spelled out in the written reason.
- Keep each `reason` and `recommendation` to 2-3 sentences. Cite specific evidence (field names, ADR IDs, pattern names) rather than restating the rubric; do not pad with extra commentary. This keeps the full 5-dimension JSON output short enough to avoid truncation.
- Always emit the complete JSON object with every dimension present and all braces/brackets closed before ending your response.
- For the `layer_responsibilities` dimension specifically:
  - Base the score solely on the dedicated `layer_responsibilities` section (or an equivalent explicit narrative assigning ownership and rationale per layer). `layers_involved` tags on workflow or contract entries are not evidence for this dimension.
  - When `layer_responsibilities` is missing or empty, the `reason` must explicitly name the missing layer responsibilities, missing explicit boundaries between layers, or missing clear responsibilities for each layer. The `recommendation` must ask to specify layer responsibilities explicitly, including ownership, boundaries, and mapping workflow changes to a layer.
  - When `layer_responsibilities` is exemplary, the `reason` must describe clear per-layer ownership, explicit boundaries, reuse of existing components, and justified deviations without naming any deficiency. The `recommendation` must not identify any concrete gap or required change; it may be empty, say no changes are needed, or offer only forward-looking advice to keep doing what the design already does.

### 3. Save the Grade
- save the grade to a new json file with the same name as the design json file, but with the suffix `.design-grade.json`.
  - If unable to write files, put the grade JSON in the chat.
- Output file MUST follow the `/schema/design-grade.schema.json` schema.

### 4. Write the Sentinel File
- create `<input_parent>/.process/` when needed and write `{skill-name}.done.json` there; use the repository-root `.process/` only when no input path is supplied. The sentinel must not be removed after verification.
- the sentinel file will follow @/schema/sentinel.schema.json. 
- set the task field to "{skill-name}".
- the verify_params of the sentinel file will follow @/schema/verify-params.schema.json. 
- set the verify_params as follows:
    - set "design_grade_path" as the path to the design grade file  relative to repo root.


