---
name: draft-implementation-plan
description: Drafts a high-level implementation plan based on the extracted story document
---

## Steps:
### 1. Read the Story Analysis Document
- Read the story analysis json document.

### 2. Create Plan JSON File
- create a new json file in the same directory as the extracted intent json document, using the same filename but with the suffix `.plan.json`. e.g. "create-object-with-validation.plan.json"
- The json will follow `/schema/plan.schema.json`. 
- set the source_story to the file path of the story analysis json document.

### 3. Identify the Workstreams
- Review the Repository, and identify the key application layers such as UI, API, Database, External Services, etc.
- Identify the layers and components that will be affected by this implementation.
- populate the "impacted_layers" field in the plan json file.

### 4. Draft Implementation Plan

```
Outline high-level approach, and the layer each of the steps belong to:

IMPLEMENTATION PLAN:
1. [First major step]
2. [Second major step]
3. [Third major step]
...
```

Update the "steps" field in the plan json file.

### 5. Draft Testing Strategy

```
Outline the testing strategy, and the layer each of the test belong to, based on the AC:
TESTING STRATEGY:
├── Unit tests: [Key behaviors to test]
├── Integration tests: [System interactions]
└── E2E tests: [User scenarios]
```

Update the "testing_strategy" field in the plan json file.

### 6. Draft Risks and Mitigations

```
Outline the risks and mitigations, and the layer each of the mitigation would be applied in:

RISKS AND MITIGATIONS:
├── Risk 1: [Description]
│   └── Mitigation: [Approach]
└── Risk 2: [Description]
    └── Mitigation: [Approach]
```

Update the "risks_and_mitigations" field in the plan json file.

### 7. Write the Sentinel File
- create a sentinel file in the `.process` directory, named `{skill-name}.done.json`.
- the sentinel file will follow @/schema/sentinel.schema.json. 
- set the task field to "{skill-name}".
- the verify_params of the sentinel file will follow @/schema/verify-params.schema.json. 
- set the verify_params as follows:
    - set "plan_path" as the path to the plan file relative to repo root.


