# SDLC Design Workflow

## Purpose
Design a user story implementation with architecture and design patterns.

## Trigger
- Starting a new feature or bug fix
- Before writing any production code
- After Requirements have been Clarified

## Inputs Required
- Analysis of incoming requirements
- Relevant domain context

## Workflow Steps

### Step 1: Assess Current Reality
Assess Current Reality, to identify what's already in place and what needs to be built, existing ADRs, and design precedents, and architecture. using the `audit-current-reality` skill. 

Address any verification errors before proceeding. 

### Step 2: Add Design Step prior to Plan
Design the stories implementation with the `design-story-implementation` skill, with the analysis and audit files from the previous steps. 

Address any verification errors before proceeding. 

### Step 3: Grade the Design
grade the design based on the Design Quality Rubric using the `grade-story-design` skill on the design file from the previous step.

Address any verification errors before proceeding. 