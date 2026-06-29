---
name: extract-story-intent
description: Extract a user story from a given document or text, into a json format
---


## Steps:
### 1. Read the Provided Document/Text
- Read the provided document or text. You will be extracting information from this document to create the user story JSON. 

### 2. Create JSON File
- create a new json object
- The json will follow `/schema/story-intent.schema.json`. 
- set the "rawRequest" to the file path, relative to repo root, of the provided document, or to the verbatim text provided if no document was sent.

### 3. Extract User Story
```
Extract components from the story format:

SO THAT [benefit]    → Why? What value does this provide?
AS A [role]          → Who is the user? What's their context?
I WANT [capability]  → What feature/behavior is requested?
```

Fill in the appropriate section of the json with this information

### 4. Extract Target Persona
```
Document the target persona:

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


Fill in the appropriate section of the json with this information


### 5. Extract Capability Breakdown
```
Break down what's being requested:

CAPABILITY ANALYSIS:
├── Core action: [The main thing user does]
├── Inputs required: [What data is needed?]
├── Outputs expected: [What should result?]
├── State changes: [What data is modified?]
└── Side effects: [Notifications, logs, etc.]
```

Fill in the appropriate section of the JSON. Leave the affected components empty for now. 

### 6. Extract the Listed Acceptance Criteria
```Extract the acceptance criteria from the story format:

For each extract:
- verbatim criteria
- gherkin/scenario expression
- type {functional, non-functional, business rule, constraint}
- job to be done (jtbd) in Verb Object Context format if possible
- persona served
```

Fill in the appropriate section of the JSON. 

### 7. Return the JSON Object
- Return the completed JSON object to the user in a code snippet (```json {object here}```)