# Leave the Sentinel and Co-locate `.process`

## Bottom line
Skill sentinel files must remain on disk after verification. They must be written to a `.process` directory under the same parent as the skill's first input document. The repository root `.process` directory is the fallback when no input path is supplied.

## Decision
Use the repo root `.process` directory only as a fallback. When `input_paths` is non-empty, the canonical sentinel location is `<input_parent>/.process/<skill-name>.done.json`.

## Rationale
- The post-edit verification hook can run before `SkillActivity.execute` finishes. Consuming (deleting) the sentinel created a race where the Activity had to fall back to the expected output path and emit a warning.
- Keeping sentinels on disk lets the Activity treat a missing sentinel after a successful harness run as a real failure again.
- Co-locating the sentinel with the input/output document keeps workflow artifacts grouped by source document instead of all piling into the top-level `.process` directory.

## Requirements

### 1. Skill instructions
Every skill that writes a sentinel must instruct the agent to create it in a `.process` folder under the same parent as the input document, named `{skill-name}.done.json`, and must not tell the agent to delete the sentinel after verification.

### 2. Verify scripts
Every `verify.sh` must read the sentinel, validate the artifact, and leave the sentinel in place. `rm -f "$sentinel_path"` or any equivalent must be removed from all `verify.sh` scripts.

### 3. `skill_activity.py`
- Derive the default sentinel path as `Path(input_paths[0]).parent / ".process" / f"{skill_name}.done.json"` when `input_paths` is non-empty.
- Fall back to `repo_root / ".process" / f"{skill_name}.done.json"` when `input_paths` is empty.
- Delete only a stale sentinel before invocation, not after.
- Add a prompt instruction for the agent to write the sentinel into the co-located `.process` directory.
- Apply the same fallback logic to the standalone `run_skill` helper.

### 4. Tests and fake harness
- `tests/fake_harness.py` must write the sentinel next to the first input, not into the repository root `.process`.
- Unit tests that assert root `.process` sentinel paths must be updated to co-located paths, or use `input_paths` that trigger the fallback case.

### 5. Hook
`.devin/scripts/post-edit-verify-skill.sh` already matches `*/.process/*.done.json`, but the comment and any path assumptions in the hook config should be updated to clarify that sentinels are now co-located and not consumed.
