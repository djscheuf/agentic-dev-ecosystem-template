# Analyze User Story Workflow

## Purpose
Systematically analyze a user story to understand requirements, identify edge cases, assess complexity, and prepare for implementation.

## Workflow Steps

### Step 1: Parse the User Story
extract user-story from the provided document or prompt using the `extract-story-intent` skill.

Address any verification errors before proceeding. 

### Step 2: Analyze the User Story
expand the user-story into a comprehensive analysis document using the `expand-story-analysis` skill on the extracted intent file from the previous step.

Address any verification errors before proceeding. 

### Step 3: Draft Implementation Plan
draft a high-level implementation plan based on the extracted story document using the `draft-impl-plan` skill on the analysis file from the previous step.

Address any verification errors before proceeding. 

### Step 4: Break out Workstream Plans
break out the implementation plan into workstream plans using the `create-workstream-plans` skill on the implementation plan file from the previous step.

Address any verification errors before proceeding. 