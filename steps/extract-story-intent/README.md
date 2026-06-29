# Extract Story Intent Step

This step extracts a user story from a provided document or text into a structured JSON format.

## Structure

```
extract-story-intent/
├── step.json           # Step definition for orchestrator
├── prompt.md           # Prompt instructions for the agent
├── scripts/
│   └── verify.sh       # Verification script
└── schema/
    ├── story-intent.schema.json    # JSON schema for output
    ├── sentinel.schema.json        # (legacy, not used by devin_wrapper)
    └── verify-params.schema.json   # (legacy, not used by devin_wrapper)
```

## Usage

Execute this step using the devin_wrapper:

```bash
python orchestrator/devin_wrapper.py steps/extract-story-intent/step.json <input_document>
```

## Step Configuration

- **Model**: claude-sonnet-4
- **Budget**: 100 ACUs
- **Timeout**: 300 seconds
- **Verification**: Automatic via `scripts/verify.sh`

## Verification

The verification script (`scripts/verify.sh`) validates:

1. **Structure**: JSON follows the schema with all required properties
2. **Completeness**: All required fields are populated (not null)
3. **Consistency**: Target persona is served by at least one acceptance criterion

### Exit Codes

- `0`: Verification passed
- `2`: Verification failed (self-correction needed - agent will retry)

## Key Changes from Skill Version

1. **No Sentinel Files**: The devin_wrapper doesn't use sentinel files for verification
2. **Auto-discovery**: Verification script automatically finds `*.intent.json` files
3. **Simplified Flow**: Removed `.process/` directory dependency
4. **Direct Execution**: Can be called directly by orchestrator without manual sentinel management

## Output

The step creates a JSON file named `{verb-object-context}.intent.json` containing:

- Raw request reference
- Story title
- User story (as_a, i_want, so_that)
- Target persona details
- Capability breakdown
- Acceptance criteria with Gherkin scenarios
