# Analyze Story

Analyze the extracted story document, capturing capability, acceptance criteria, edge cases, dependencies and open design questions.

## Steps

### 1. Read the Extracted Intent
- Read the extracted intent JSON document provided via `previous_step_output`.

### 2. Read the provided document
- Read the contents of the raw_prompt field in the extracted intent JSON document, either the file under the provided path or the verbatim text.

### 3. Create Analysis JSON File
- Create a new JSON file in the same directory as the extracted intent JSON document, using the same filename but with the suffix `.analysis.json`. e.g. "create-object-with-validation.analysis.json"
- The JSON will follow `schema/analysis.schema.json`.
- Set the raw_request to the file path, relative to repo root, of the provided document, or to the verbatim text provided if no document was sent.

### 4. Analyze the Capability
```
Break down what's being requested:

CAPABILITY ANALYSIS:
├── Core action: [The main thing user does]
├── Inputs required: [What data is needed?]
├── Outputs expected: [What should result?]
├── State changes: [What data is modified?]
└── Side effects: [Notifications, logs, etc.]

Map to system components:
├── UI affected: [Screens, forms, buttons]
├── API endpoints: [New or modified]
├── Database changes: [Schema, queries]
└── External services: [Third-party integrations]
```

Fill in the appropriate section of the JSON.

### 5. Examine Acceptance Criteria
```
For each acceptance criterion:
- review the extracted criterion
- confirm testability, re-write scenario if not testable
- identify dependencies, that is other criteria this relates to

Ensure we have acceptance criteria for happy path, error handling, boundary conditions, and permission/access scenarios. Generate them if missing.
```

### 6. Identify Edge Cases
```
Systematically consider:

INPUT EDGE CASES:
□ Empty/null values
□ Maximum length inputs
□ Special characters (unicode, emojis)
□ Invalid formats
□ Boundary values

STATE EDGE CASES:
□ First-time use (no existing data)
□ Maximum data limits
□ Concurrent modifications
□ Partial completion states

USER EDGE CASES:
□ No permissions
□ Expired sessions
□ Multiple devices
□ Interrupted workflows

SYSTEM EDGE CASES:
□ External service unavailable
□ Network timeout
□ Database errors
□ Rate limiting

And capture criteria for each edge case under edge_cases section.
```

### 7. Identify Dependencies
```
Identify what this story depends on:

TECHNICAL DEPENDENCIES:
├── Existing code: [Classes, services to modify]
├── New code: [What needs to be created]
├── Infrastructure: [Databases, queues, etc.]
└── External services: [APIs, integrations]

STORY DEPENDENCIES:
├── Blocked by: [Stories that must complete first]
├── Blocks: [Stories waiting on this]
└── Related: [Stories that share components]

KNOWLEDGE DEPENDENCIES:
├── Domain knowledge needed: [Business rules to learn]
├── Technical knowledge needed: [Technologies to understand]
└── Questions for stakeholders: [Clarifications needed]

Capture the dependencies in the appropriate section of the JSON.
```

### 8. Identify Open Questions
When implementation or approach questions are identified, capture them in the appropriate section of the JSON. Capture the areas or aspects impacted by the question. For example a question about authentication flow might impact security, user experience, and integration points.

## Output Requirements

The output JSON file must:
- Be valid JSON
- Follow the schema structure in `schema/analysis.schema.json`
- Include all required fields
- Have at least one acceptance criterion
- Have the target persona served by at least one acceptance criterion
