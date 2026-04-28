---
name: create-workstream-plans
description: Converts a High-level Implementation Plan into several parallel Workstream documents
---

## Steps:
### 1. Read the Story Analysis Document
- Read the story analysis json document.

### 2. Read the Draft Implementation Plan
- Read the draft implementation plan json document.


### 3: Identify Work Streams
```
Break the work into parallel tracks:

TYPICAL WORK STREAMS:
├── Foundations
│   ├── Contracts and Interfaces Defined
│   ├── Database migrations
│   ├── Data model changes
│   ├── API endpoint Stubbed with fake response data
│   └── Frontend API calls to stubbed endpoints
├── Backend/API
│   ├── Repositories, and Handlers
│   ├── Business logic
│   └── API endpoints fully built
├── Frontend/UI
│   ├── Components
│   ├── State management
│   └── Completed API integration
├── Infrastructure
│   ├── Configuration
│   └── Deployment
└── Testing
    ├── Integration tests
    └── E2E tests

The Foundations workstreams purpose is to enable parallel development of the rest of the feature. 
```

### 5. Create Workstream Directories

Create a subdirectory `streams` under the same folder that contains the story analysis and plan json documents.

### 5. Create Workstreams
For each workstream, complete the following steps. 

#### 5.1 Create Workstream Document
Create a workstream json document. The workstream document will follow the schema in `schema/workstream.schema.json`. The document should be named `{workstream-name}.stream.json` and placed under the `streams` subdirectory.

### 5.1 Identify Stream-related Criteria
Copy the Acceptance Criteria and Edge Cases from the analysis document that are related to the workstream's scope to the "related_acceptance_criteria" and "related_edge_cases" fields in the workstream json document.

### 5.2 Identify Stream Dependencies
Identify any dependencies that the workstream has on other workstreams. Update the "dependencies" field in the workstream json file.
Dependencies can include completion of other workstreams, or specific artifacts from other workstreams.

### 5.3 Outline Stream Implementation Plan

```
Outline high-level approach:

IMPLEMENTATION PLAN:
1. [First major step]
2. [Second major step]
3. [Third major step]
...

And for each step identify what artifacts are needed to complete the step.
```

Update the "steps" field in the workstream json file, including each steps dependencies. 

### 5.4 Identify Relevant Context

Based on the scope of the stream, and the related criteria, identify any relevant context that should be included in the workstream document. It may be helpful to review the analysis document and especially the questions section. 

Relevant context should include documentation such as ADRs, design documents, existing code components, and any other relevant content.

Mark these in the "relevant_context" field of the workstream json file.

### 6. Capture Streams Index

Create a file `streams.index.json` in the same directory as the analysis and plan json documents. It will follow the `schemas/streams-index.schema.json` schema. This file will index all the workstreams, including their names, descriptions, and paths to their respective json documents.

### 7. Write the Sentinel File
- create a sentinel file in the `.process` directory, named `{skill-name}.done.json`.
- the sentinel file will follow @/schema/sentinel.schema.json. 
- set the task field to "{skill-name}".
- the verify_params of the sentinel file will follow @/schema/verify-params.schema.json. 
- set the verify_params as follows:
    - set "steam_index_path" as the path to the streams index file  relative to repo root.
    - set "workstream_paths" as an array of paths to all the workstream plan files relative to repo root.


