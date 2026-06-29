# Improve Story Analysis

Review the analysis grade, and improve the analysis if needed.

**Grade Document**: {{previous_step_output}}

## Steps

### 1. Read the Grade Document
- Read the grade document at: {{previous_step_output}}

### 2. Read the provided document
- Read the contents of the analysis_file_path field in the grade document, either the file under the provided path or the verbatim text.

### 3. Update Analysis JSON File
- Update and Improve the Analysis document based on the grader feedback. 

## Output Requirements
The output JSON file must:
- Be valid JSON
- Follow the schema structure in `schema/analysis.schema.json`
- Include all required fields
- Have at least one acceptance criterion
- Have the target persona served by at least one acceptance criterion
