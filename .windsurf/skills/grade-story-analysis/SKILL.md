---
name: grade-story-analysis
description: Grades the quality of the extracted story document with additional details based on the User Story Quality Rubric
---

## Steps:
### 1. Read the Analysis JSON
- Read the analysis json document. The analysis will follow `/schema/analysis.schema.json`.

### 2. Grade the Analysis
- grade the analysis based on the User Story Quality Rubric defined in `/rubric.md`.
- Identify a score for each dimension and provide your reasoning for that score. 
- Provide recommendations for improvement for each dimension with an imperfect score.

### 3. Save the Grade
- save the grade to a new json file with the same name as the analysis json file, but with the suffix `.analysis-grade.json`. This file must follow the `/schema/analysis-grade.schema.json` schema.

### 4. Write the Sentinel File
- create a sentinel file in the `.process` directory, named `{skill-name}.done.json`.
- the sentinel file will follow @/schema/sentinel.schema.json. 
- set the task field to "{skill-name}".
- the verify_params of the sentinel file will follow @/schema/verify-params.schema.json. 
- set the verify_params as follows:
    - set "analysis_grade_path" as the path to the analysis grade file  relative to repo root.


