# Saga State Enrichment for Step Prompts

## Overview

Enhance the Saga orchestration system so that step prompts can be enriched with Saga state variables at invocation time. The orchestrator is responsible for enrichment, not the wrapper. This allows subsequent agents to reference context about the Saga execution (e.g., where state is stored, what the previous step produced) without requiring external lookups.

The enrichment mechanism uses a single named variable `previous_step_output` that is updated after each completed step. In addition, all step outputs are logged separately for reconstruction of any step's context from the Saga log.

## Core Requirements

### 1. Prompt Enrichment Dictionary

The orchestrator maintains a prompt enrichment dictionary with the following initial variables:

- **Saga ID**: Unique identifier for the current Saga execution
- **State Storage Location**: File system path where the Saga's state is persisted
- **Initial Prompt Path**: Derived from the initial Saga input; the working directory for documents
- **Custom variables**: Arbitrary additional variables (e.g., "Code Directory") defined in the Saga definition

The complete prompt enrichment dictionary is stored as part of the Saga state (as JSON in the state directory) and is available to verify scripts and for prompt substitution.

### 2. Prompt Enrichment Mechanism

- The orchestrator enriches step prompts with Saga state context before DevinWrapper invocation
- Variable substitution happens at the orchestration layer, not at the wrapper level
- Substitution uses the prompt enrichment dictionary to replace variables in the prompt template

### 3. Previous Step Output Variable

- A single named variable `previous_step_output` is updated after each completed step
- This variable contains the output from the previous step's verify script
- It is available for substitution in subsequent step prompts
- When a child Saga resolves, its output (from its verify script) becomes the parent Saga's `previous_step_output`

### 4. Step Output Logging

- All step outputs are logged separately as part of Saga execution
- This log enables reconstruction of `previous_step_output` for any given step from the Saga log
- Step output logging is separate from the `previous_step_output` variable mechanism
- (Full step output log design is out of scope for this initial requirement)

### 5. Saga State Persistence

- The prompt enrichment dictionary is persisted as JSON in the Saga's state directory
- This enables Saga resumption: when a Saga is resumed, the enrichment dictionary is restored
- The `previous_step_output` variable is also persisted as part of Saga state

### 6. Verify Script Contract

All verify scripts receive the following parameters:

- **Saga process state directory**: Path to the Saga's state directory (contains enrichment dictionary and other state)
- **Prompt enrichment dictionary path**: Path to the JSON file containing the enrichment dictionary

Verify script behavior:

- Returns exit code 0 for success, non-zero for failure
- Outputs content to stdout that becomes the `previous_step_output` for the next step
- Can access the enrichment dictionary (as JSON) to derive working directories and other context
- On failure, outputs an error message that is captured and used to enrich the follow-on prompt

Example: Extract Story Intent verify script

- Receives the Saga state directory and enrichment dictionary path
- Reads the enrichment dictionary to get `initial_prompt_path`
- Derives the working directory for documents from `initial_prompt_path`
- Searches for the expected extracted intent file in the working directory
- On success: outputs the path to the extracted intent file (becomes `previous_step_output`)
- On failure: outputs a descriptive error message (e.g., "Expected intent file not found in {working_directory}")

### 7. Child Saga Integration

- When a child Saga completes, its verify script output becomes the parent Saga's `previous_step_output`
- This enables chaining of Saga results through the step output mechanism

## Handling Nondeterministic AI Actions

When AI agents produce outputs in unpredictable locations:

1. **Tight Saga state control**: The Saga orchestration should tightly control where outputs are placed
2. **Verification failure as feedback**: If an output is placed in an undesirable location, verification will fail
3. **Descriptive error messages**: Verification failures should provide clear messages about what went wrong
   - Example: "Expected intent file not found in {working_directory}"
   - These messages are captured and used to enrich the follow-on prompt, guiding the agent to correct behavior

This approach uses verification failure as a feedback mechanism to train agents toward correct output placement.

## Implementation Scope

1. Define the prompt enrichment dictionary data structure
2. Add method to orchestrator to build and persist the enrichment dictionary
3. Add method to orchestrator to enrich step prompts using the dictionary
4. Update Saga state persistence to include the enrichment dictionary
5. Update verify script invocation to pass state directory and enrichment dictionary path
6. Implement `previous_step_output` capture and propagation after each step
7. Persist `previous_step_output` as part of Saga state
8. Update Extract Story Intent verify script to use new contract
9. Add support for Saga-level verify scripts (optional, for future use)
10. Add step output logging to Saga execution (separate from `previous_step_output`)

## Saga Definition Changes

Saga definitions should support:

- **Enrichment dictionary configuration**: Optional dictionary of custom variables to include in the enrichment dictionary
  - Example: `enrichment: { "code_directory": "/path/to/code" }`
- **Initial prompt path**: Derived from the initial Saga input (working directory for documents)

## Next Steps

- Review and validate this requirements document
- Examine the current Saga definition schema and orchestration code
- Plan implementation sequence and identify dependencies
