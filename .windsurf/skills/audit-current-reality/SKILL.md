---
name: audit-current-reality
description: Review and capture the current application reality prior to designing implementation of a new user story. Identifies relevant ADRs, existing code patterns, and target architecture. 
---

## Steps:
### 1. Read the story analysis document
- Read the story analysis document provided by the user. This document contains the user story in a structured format, as well as some basic analysis of the upcoming functionality. The document will follow the schema defined in `/schema/analysis.schema.json`.

### 2. Audit the Vault
- use the `query-wiki` tool to search for relevant information in the vault. This will include relevant ADRs, existing API contracts, personas, and target architecture.

### 3. Audit the Code
- use the `query-code` tool to search for relevant information in the codebase. This will include existing services, models, and components that may be related to the user story.

### 4. Identify the Project Structure and Tech Stack
- identify the project's organizational structure so you know where to look for relevant code and documentation, and where to place new code.
- If the project is a monorepo, identify the structure and purpose of the subprojects.
- Identify the Tech stack used in each project including the programming language, frameworks, libraries, and unit testing tools. 

### 5. Capture the Audit file
- create current reality audit file in the same folder as the given analysis json. The audit file will follow the schema defined in `/schema/audit.schema.json`. The file should be named `current-reality.audit.json`.

### 6. Write the Sentinel File
- create a sentinel file in the `.process` directory, named `{skill-name}.done.json`.
- the sentinel file will follow `/schema/sentinel.schema.json`. 
- set the task field to "{skill-name}".
- the verify_params of the sentinel file will follow `/schema/verify-params.schema.json`. 
- set the verify_params as follows:
    - set "audit_path" as the path to the audit file  relative to repo root.
