---
name: expand-story-analysi
description: Expands the extracted story document with additional details, and drafts a high-level implementation plan based on captured assumptions
---

## Steps:
### 1. Read the Extracted Intent
- Read the extracted intent json document. 

### 2. Read the provided document
- read the conents of the raw_prompt field in the extracted intent json document, either the file under the provided path or the verbatim text.

### 2. Create Analysis JSON File
- create a new json file in the same directory as the extracted intent json document, using the same filename but with the suffix `.analysis.json`. e.g. "create-object-with-validation.analysis.json"
- The json will follow `/schema/analysis.schema.json`. 
- set the raw_request to the file path of the provided document, or to the verbatim text provided if no document was sent.
### 3. Analyze the Capability
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

### 4. Examine Acceptance Criteria
```
For each acceptance criterion:
- review the extracted crietion
- confirm testability, re-write scenario if not testable
- identify dependencies, that is other criteria this relates to

Ensure we have acceprtrance criteria for happy path, error handling, boundary conditions, and permission/access scenarios. Generate them if missing. 
```

### 5. Identify Edge Case
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

### 7. Clarify Ambiguities
```
When dependencies or questions are identified:

Review existing related code, ADRs, and documentation to understand the context and make informed assumptions.
For each question, capture the following:
- the question
- your assumed answer
- the rationale for your assumption
- the basis for your assumption (e.g., "pattern seen in {existing code}", "desicion precedent in {specific ADR}", "documented business rule per {specific documentation}")
```

### 8. Draft Implementation Plan
```
Outline high-level approach:

IMPLEMENTATION PLAN:
1. [First major step]
2. [Second major step]
3. [Third major step]
...

TESTING STRATEGY:
├── Unit tests: [Key behaviors to test]
├── Integration tests: [System interactions]
└── E2E tests: [User scenarios]

RISKS AND MITIGATIONS:
├── Risk 1: [Description]
│   └── Mitigation: [Approach]
└── Risk 2: [Description]
    └── Mitigation: [Approach]
```

### 9. Write the Sentinel File
- create a sentinel file in the `.process` directory, named `{skill-name}.done.json`.
- the sentinel file will follow @/schema/sentinel.schema.json. 
- set the task field to "{skill-name}".
- the verify_params of the sentinel file will follow @/schema/verify-params.schema.json. 
- set the verify_params as follows:
    - set "analysis_path" as the path to the analysis file.


