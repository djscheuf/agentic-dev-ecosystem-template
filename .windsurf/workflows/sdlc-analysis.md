# SDLC Analysis Workflow

## Purpose
Analyze a user story to understand requirements, identify edge cases, assess complexity, and prepare for implementation.

## Trigger
- Starting a new feature or bug fix
- Before writing any production code
- When requirements need clarification

## Inputs Required
- User story or requirement description
- Acceptance criteria (if available)
- Relevant domain context

## Workflow Steps

### Step 1: Parse the User Story
extract user-story from the provided document or prompt using the `extract-story-intent` skill.

Address any verification errors before proceeding. 

### Step 2: Analyze the User Story
expand the user-story into a comprehensive analysis document using the `expand-story-analysis` skill on the extracted intent file from the previous step.

Address any verification errors before proceeding. 

### Step 3: Grade the Analysis
grade the analysis based on the User Story Quality Rubric using the `grade-story-analysis` skill on the analysis file from the previous step.

Address any verification errors before proceeding. 