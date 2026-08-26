---
name: repair-story-analysis
description: Repair the analysis of a story by re-analyzing the extracted intent, and existing analysis, and expanding on missing details, based on the grader feedback. Finally the existing analysis is updated with the expaned or clarified details.
---

## Steps:
### 1. Read the Extracted Intent
- Read the extracted intent json document. 

### 2. Read the provided document
- read the conents of the raw_prompt field in the extracted intent json document, either the file under the provided path or the verbatim text.

### 3. Read the existing Analysis
- Read the existing analysis json document, if it exists.

### 4. Read the Analysis Grade feedback
- Read the analysis grade, and recommendations. 

### 5. Update the Analysis JSON File
- Apply the grader recommendations to the Analysis if able. 
- If the grader recommendations cannot be applied, do not update the analysis. And report the failure to the chat. 
- The json will follow `/schema/analysis.schema.json`. 
- set the raw_request to the file path, relative to repo root, of the provided document, or to the verbatim text provided if no document was sent.

### 6. Write the Sentinel File
- create a sentinel file in the `.process` directory, named `{skill-name}.done.json`.
- the sentinel file will follow @/schema/sentinel.schema.json. 
- set the task field to "{skill-name}".
- the verify_params of the sentinel file will follow @/schema/verify-params.schema.json. 
- set the verify_params as follows:
    - set "analysis_path" as the path to the analysis file relative to repo root.
