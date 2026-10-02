# Analysis Test Cases

## Base Test Cases

### Basic Analysis
Given a story intent file with Story, Generic Persona, and some AC
Then the analysis should include:
- Capability analysis
- System components Impacted
- Persona analysis
- AC analysis, including AC interdependencies
- Edge cases identified
- Dependencies including technical, story, and knowledge called out
- Open questions identified
- Matches Schema

### Existing AC
Given a Story Intent with existing AC
THEN the analysis should include:
- AC analysis should identify existing AC
- AC analysis should identify new AC
- AC analysis should identify AC interdependencies

### Identified Dependencies
Given a Story Intent with clear external dependencies
THEN the analysis should include:
- Dependencies should be identified
- Dependencies should be categorized as technical, story, or knowledge
- Dependencies should be linked to the appropriate components

## Partial Slice Test Cases

## Backend Only Story
Given a Intent file that only impacts the API
THEN the analysis should include:
- System components should list backend ONLY, NO UI
- Edge cases should include backend-specific edge cases

## Frontend Only Story
Given a Intent file that only impacts the UI
THEN the analysis should include:
- System components should list frontend ONLY, NO backend
- Edge cases should include frontend-specific edge cases
