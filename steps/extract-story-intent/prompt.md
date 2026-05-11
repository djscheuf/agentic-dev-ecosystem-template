# Extract Story Intent

Extract a user story from the provided document or text into a structured JSON format.

**Input Document**: {{initial_prompt_path}}

## Steps

### 1. Read the Provided Document/Text
- Read the document at {{initial_prompt_path}}. You will be extracting information from this document to create the user story JSON.

### 2. Create JSON File
- Create a new JSON file in the same directory as the document or text, using the {Verb Object Context} of the user story as the filename. e.g. "create-object-with-validation.intent.json"
- The JSON will follow the schema at `schema/story-intent.schema.json`.
- Set the `raw_request` to the file path (relative to repo root) of the provided document, or to the verbatim text provided if no document was sent.

### 3. Extract User Story
Extract components from the story format:

```
SO THAT [benefit]    → Why? What value does this provide?
AS A [role]          → Who is the user? What's their context?
I WANT [capability]  → What feature/behavior is requested?
```

Fill in the appropriate section of the JSON with this information.

### 4. Extract Target Persona
Document the target persona:

```
USER PROFILE:
├── Persona Name: [e.g., Sarah - E-commerce Shopper]
├── Role: [e.g., Customer, Admin, Guest]
├── Technical level: [Novice/Intermediate/Expert]
├── Frequency of use: [Daily/Weekly/Occasional]
├── Environment: [Desktop/Mobile/Both]
└── Permissions: [What can they access?]

Questions to answer:
- What other actions does this user typically perform?
- What's their journey before/after this feature?
- Are there different user types affected?
```

Fill in the appropriate section of the JSON with this information.

### 5. Extract Capability Breakdown
Break down what's being requested:

```
CAPABILITY ANALYSIS:
├── Core action: [The main thing user does]
├── Inputs required: [What data is needed?]
├── Outputs expected: [What should result?]
├── State changes: [What data is modified?]
└── Side effects: [Notifications, logs, etc.]
```

Fill in the appropriate section of the JSON. Leave the `affected_components` empty for now.

### 6. Extract the Listed Acceptance Criteria
Extract the acceptance criteria from the story format:

For each criterion extract:
- Verbatim criterion text
- Gherkin/scenario expression
- Type: {Functional, Non-functional, Happy path, Error handling, Edge Case}
- Job to be done (JTBD) in Verb Object Context format if possible
- Persona served

Fill in the appropriate section of the JSON.

### 7. Write the Sentinel File
Create a new file called `extract-story-intent.done.json`, following the `schema/sentinel.schema.json` schema. Put this file under `saga-{{SAGA_ID}}` directory.
- Set the `step_name` to `extract-story-intent`
- Set the `status` to `completed`
- Set the `verify_params` property to an object with the `extracted_intent_path` field set to the path of the extracted intent file, and the `reference_document` field set to the `{{initial_prompt_path}}`.

## Output Requirements

The output JSON file must:
- Be valid JSON
- Follow the schema structure in `schema/story-intent.schema.json`
- Include all required fields
- Have at least one acceptance criterion
- Have the target persona served by at least one acceptance criterion
