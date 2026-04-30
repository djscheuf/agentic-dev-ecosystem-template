---
description: Systematically analyze a user story to understand requirements, identify edge cases, assess complexity, Then prepare Design an approach based on suitable architecture and design patterns, and Plan implementation steps. 
---
# SDLC - Software Delivery Lifecycle

## Workflow Steps

### Advisory
- This workflow is composed of subworkflows and specific skills. Adhere closely to the skill instructions and guidelines.
- It is Critical to write the Sentinel file for each skill to track progress and ensure execution quality.


### Phase 1: Analysis
Input: User Story Document or Prompt
Workflow: /sdlc-analysis
Output: Analysis Document

```
Execute: sdlc-analysis
├── Understand requirement
├── Analyze requirements
├── Identify edge cases
├── Assess complexity
└── Output: Analysis document
```

### Phase 2: Design
Input: Analysis Document
Workflow: /sdlc-design
Output: Design Document

```
Execute: sdlc-design
├── Understand requirement, and analysis
├── Audit Current Application State
├── Determine suitable architecture and design patterns
├── Design Implementation Approach
└── Output: Design document
```

### Phase 3: Plan
Input: Design Document
Workflow: /sdlc-plan
Output: Workstream Plan Documents

```
Execute: sdlc-plan
├── Understand requirements, and design
├── Design Implementation Approach
├── Identify Implementation Steps and dependencies
├── Break down into workstreams
└── Output: Several Workstream Plan documents
```

### Phase 4: Implement
Input: Workstream Plan Documents
Output: Clean code, all tests passing
Skip this step for now. 
// TODO: Add SDLC Implement workflow
