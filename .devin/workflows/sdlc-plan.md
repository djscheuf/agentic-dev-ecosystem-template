# SDLC Plan Workflow

## Purpose
Plan a user story implementation from design, and split into workstreams based on dependencies.

## Trigger
- Starting a new feature or bug fix
- Before writing any production code
- After Designing Approach with suitable architecture and design patterns

## Inputs Required
- Design of the user story
- Relevant domain context

## Workflow Steps

### Step 1: Draft Implementation Plan
draft a high-level implementation plan based on the extracted story document using the `draft-implementation-plan` skill on the analysis file from the previous step.

Address any verification errors before proceeding. 

### Step 2: Break out Workstream Plans
break out the implementation plan into workstream plans using the `split-plan-into-workstreams` skill on the implementation plan file from the previous step.

Address any verification errors before proceeding. 

### Step 3: Grade Workstream Plans
Skip this step for now. 
// TODO: Add Qualitative Verification Step