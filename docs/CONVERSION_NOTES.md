# Conversion Notes: Skill to Step

This document describes the conversion of `extract-story-intent` from a Windsurf skill to an orchestrator step.

## Key Differences

### 1. Execution Model

**Skill (Original)**:
- Executed within Windsurf IDE context
- Uses `.process/` directory for sentinel files
- Verification reads sentinel file to find output location
- Manual cleanup of sentinel files

**Step (New)**:
- Executed via `devin_wrapper.py` orchestrator
- No sentinel files required
- Verification auto-discovers output files
- Cleaner execution flow

### 2. Verification Script Changes

**Original (`verify.sh`)**:
```bash
main() {
  local sentinel_path="$1"
  # Extract story path from sentinel
  story_path=$(jq -r '.verify_params.extracted_intent_path' "$sentinel_path")
  # ... verification logic ...
  rm -f "$sentinel_path"  # Cleanup sentinel
}
```

**New (`scripts/verify.sh`)**:
```bash
find_intent_file() {
  # Auto-discover *.intent.json files
  find "$search_dir" -name "*.intent.json" -type f
}

main() {
  story_path=$(find_intent_file)
  # ... verification logic ...
  # No sentinel cleanup needed
}
```

### 3. File Structure

**Skill Structure**:
```
.windsurf/skills/extract-story-intent/
├── SKILL.md              # Skill definition + instructions
├── verify.sh             # Verification script
└── schema/               # JSON schemas
```

**Step Structure**:
```
steps/extract-story-intent/
├── step.json             # Step definition (metadata)
├── prompt.md             # Prompt instructions (separated)
├── scripts/
│   └── verify.sh         # Verification script
└── schema/               # JSON schemas (copied)
```

### 4. Prompt Content

**Skill**: Instructions embedded in `SKILL.md` with YAML frontmatter
**Step**: Instructions in separate `prompt.md` file, referenced by `step.json`

This separation allows:
- Easier prompt versioning
- Reusable step definitions
- Cleaner orchestrator integration

### 5. Integration with devin_wrapper

The `devin_wrapper.py` handles:
- Reading `step.json` configuration
- Loading prompt from `prompt.md`
- Executing Devin with appropriate model/budget/timeout
- Running verification script
- Interpreting exit codes (0=pass, 2=retry)

### 6. Exit Code Semantics

Both versions use the same exit code semantics:
- `0`: Verification passed
- `1`: Hard failure (not used in this step)
- `2`: Self-correction needed (agent should retry)

### 7. Removed Dependencies

The step version removes:
- Dependency on `.process/` directory
- Sentinel file creation/management
- Manual file path passing to verification

### 8. Schema Files

Schema files are copied as-is:
- `story-intent.schema.json`: Main output schema
- `sentinel.schema.json`: Kept for reference (not used)
- `verify-params.schema.json`: Kept for reference (not used)

## Benefits of Step Conversion

1. **Cleaner Execution**: No sentinel file management
2. **Better Orchestration**: Direct integration with saga executor
3. **Simpler Verification**: Auto-discovery of output files
4. **Reusability**: Can be composed into larger workflows
5. **Standardization**: Follows orchestrator conventions

## Usage Comparison

**Skill (Windsurf)**:
```
User invokes skill via Windsurf UI
→ Agent follows SKILL.md instructions
→ Agent creates sentinel file in .process/
→ User runs verify.sh with sentinel path
→ Sentinel cleaned up
```

**Step (Orchestrator)**:
```bash
python orchestrator/devin_wrapper.py \
  steps/extract-story-intent/step.json \
  docs/my-story.md
→ Devin executes with prompt.md
→ Verification runs automatically
→ Exit code indicates success/retry
```

## Migration Path

To convert other skills to steps:

1. Create `steps/<skill-name>/` directory
2. Create `step.json` with metadata
3. Extract instructions to `prompt.md`
4. Copy/adapt verification script to `scripts/verify.sh`
5. Update verification to auto-discover outputs (no sentinels)
6. Copy schema files if needed
7. Test with `devin_wrapper.py`
