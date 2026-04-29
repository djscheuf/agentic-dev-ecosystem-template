---
name: current-reality-audit
description: Review and capture the current application reality prior to designing implementation of a new user story. Identifies relevant ADRs, existing code patterns, and target architecture. 
---

## Steps:
### 1. Read the story analysis document
- Read the story analysis document provided by the user. This document contains the user story in a structured format, as well as some basic analysis of the upcoming functionality. The document will follow the schema defined in `/schema/analysis.schema.json`.

### 2. Audit the Vault
- use the `wiki-query` tool to search for relevant information in the vault. This will include relevant ADRs, existing API contracts, personas, and target architecture.

### 3. Audit the Code
- use the `code-query` tool to search for relevant information in the codebase. This will include existing services, models, and components that may be related to the user story.

### 4. Capture the Audit file
- create current reality audit file in the same folder as the given analysis json. The audit file will follow the schema defined in `/schema/audit.schema.json`. The file should be named `current-reality.audit.json`.

### 7. Write the Sentinel File
- create a sentinel file in the `.process` directory, named `{skill-name}.done.json`.
- the sentinel file will follow `/schema/sentinel.schema.json`. 
- set the task field to "{skill-name}".
- the verify_params of the sentinel file will follow `/schema/verify-params.schema.json`. 
- set the verify_params as follows:
    - set "audit_path" as the path to the audit file  relative to repo root.
