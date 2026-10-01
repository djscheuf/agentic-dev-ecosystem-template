---
name: git-rebase
description: How to rebase your feature branch onto the latest main for a clean, linear history. Use this skill when preparing branches for PR creation, updating feature branches with latest main changes, cleaning up commit history before review, handling rebase conflicts, or working on personal feature branches. Provides guided workflows for safe rebasing with pre-flight checks, conflict handling strategies, and force-push guidance. Make sure to use this skill whenever rebasing is needed, even if the user just says "update my branch" or "sync with main" - rebasing requires careful conflict resolution and verification steps.
---

# Git Rebase

This skill guides you through rebasing your feature branch onto the latest main for a clean, linear history.

## When to Use This Skill

- Preparing branches before creating a PR
- Updating feature branch with latest main changes
- Cleaning up commit history before review
- Syncing personal branches with main
- Handling rebase conflicts
- Interactive rebase for commit cleanup

## When to Use Rebase

**✅ Good Use Cases:**
- **Before creating a PR** - Clean history before review
- **Updating feature branch** - Alternative to merge for cleaner history
- **Personal branches** - When you're the only one working on the branch
- **Syncing with main** - Keep your branch up-to-date with latest changes

**❌ When NOT to Rebase:**
- **Shared branches** - Never rebase branches others are working on
- **Already pushed commits** - Changes history that others may have
- **After merge commits** - Can cause complex conflicts
- **On main/master** - Never rebase the main branch itself

## Basic Usage

### Standard Rebase
```bash
# Rebase current branch onto main
git fetch origin main
git rebase origin/main
```

### With Conflict Handling
```bash
# Continue after resolving conflicts
git add <resolved-files>
git rebase --continue

# Abort rebase in progress
git rebase --abort

# Skip current commit (use cautiously)
git rebase --skip
```

### Force Push After Rebase
```bash
# Safer force push (recommended)
git push --force-with-lease

# Standard force push (use with caution)
git push --force
```

## Rebase Workflow

### Step 1: Pre-flight Checks

**Check current branch:**
```bash
git branch --show-current
```

**Verify not on main/master:**
- Cannot rebase main onto itself
- Must be on a feature branch

**Check for uncommitted changes:**
```bash
git status
```

**If you have uncommitted changes:**
```bash
# Option A: Stash changes
git stash save "WIP: description"

# Option B: Commit changes
git add .
git commit -m "WIP: checkpoint"
```

### Step 2: Update Target Branch

**Fetch latest main:**
```bash
git fetch origin main
```

**Preview what will be rebased:**
```bash
# Count commits to be rebased
git log --oneline origin/main..HEAD

# Show commit details
git log origin/main..HEAD
```

### Step 3: Preview Potential Conflicts

**Check files modified in both branches:**
```bash
git diff --name-only origin/main...HEAD
```

This shows files that might conflict during rebase.

### Step 4: Execute Rebase

**Standard rebase:**
```bash
git rebase origin/main
```

**Interactive rebase (for advanced cleanup):**
```bash
git rebase -i origin/main
```

### Step 5: Handle Result

#### ✅ Successful Rebase
```
Successfully rebased and updated refs/heads/feat/your-branch.
```

**Next steps:**
1. **Verify UI changes still work:**
   ```bash
   cd src/ui
   pnpm run build
   pnpm test
   ```

2. **Verify API changes still work:**
   ```bash
   cd src/api
   dotnet build
   dotnet test
   ```

3. **Force push to remote:**
   ```bash
   git push --force-with-lease
   ```

#### ℹ️ Already Up To Date
```
Current branch feat/your-branch is up to date.
```

No action needed - your branch is already based on latest main.

#### ⚠️ Rebase Conflicts

**Conflict message:**
```
CONFLICT (content): Merge conflict in src/file.ts
error: could not apply abc1234... Your commit message
```

**Resolution steps:**

1. **View conflicting files:**
   ```bash
   git status
   ```

2. **Edit conflicting files** - Look for conflict markers:
   ```typescript
   <<<<<<< HEAD (origin/main)
   // Code from main
   =======
   // Your code
   >>>>>>> abc1234 (Your commit message)
   ```

3. **Resolve conflicts** - See "Conflict Resolution Strategy" section below

4. **Mark as resolved:**
   ```bash
   git add <resolved-files>
   ```

5. **Continue rebase:**
   ```bash
   git rebase --continue
   ```

6. **Repeat** if more conflicts occur

**If you get stuck:**
```bash
# Abort and return to pre-rebase state
git rebase --abort
```

## Conflict Resolution Strategy

### Understanding Rebase Conflicts

When rebasing, Git replays your branch commits **on top of** the latest main. Conflicts occur when:
- Same lines modified in both main and your branch
- Files moved/deleted in main but modified in your branch
- Files created with same name in both branches

### Standard Rebase Goal: Keep Your Branch Changes

**Most common scenario:** You want to:
1. ✅ Take ALL changes from main (the new base)
2. ✅ Apply ALL your branch changes on top
3. ✅ Keep your branch changes when conflicts occur

### Conflict Markers Explained

```typescript
<<<<<<< HEAD (origin/main)
// Code from main - the NEW base you're rebasing onto
const value = "from main";
=======
// Code from YOUR branch - what you want to keep
const value = "from my feature";
>>>>>>> abc1234 (Your commit: Add feature)
```

**To keep your branch changes:**
1. Delete the conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`)
2. Delete the main code (between `<<<<<<< HEAD` and `=======`)
3. Keep your branch code (between `=======` and `>>>>>>>`)

**Result:**
```typescript
// Code from YOUR branch - what you want to keep
const value = "from my feature";
```

### Resolution Patterns

#### Pattern 1: Keep Your Changes (Most Common)
```typescript
// BEFORE (conflict)
<<<<<<< HEAD
function oldImplementation() {
  return "main version";
}
=======
function newImplementation() {
  return "your feature version";
}
>>>>>>> abc1234

// AFTER (resolved - keep your changes)
function newImplementation() {
  return "your feature version";
}
```

#### Pattern 2: Keep Both (Merge Changes)
```typescript
// BEFORE (conflict)
<<<<<<< HEAD
import { ComponentA } from './a';
=======
import { ComponentB } from './b';
>>>>>>> abc1234

// AFTER (resolved - keep both imports)
import { ComponentA } from './a';
import { ComponentB } from './b';
```

#### Pattern 3: Keep Main Changes (Rare)
```typescript
// BEFORE (conflict)
<<<<<<< HEAD
const API_URL = "https://new-api.example.com"; // Updated in main
=======
const API_URL = "https://old-api.example.com"; // Your branch
>>>>>>> abc1234

// AFTER (resolved - keep main's update)
const API_URL = "https://new-api.example.com"; // Updated in main
```

### Quick Resolution Commands

**Accept all your changes (theirs strategy):**
```bash
# For specific file - keep YOUR branch version
git checkout --theirs <file>
git add <file>
```

**Accept all main changes (ours strategy):**
```bash
# For specific file - keep MAIN version
git checkout --ours <file>
git add <file>
```

**⚠️ Note:** During rebase, "ours" = main (base), "theirs" = your branch (confusing but true!)

### Step-by-Step Conflict Resolution

**1. Identify conflicting files:**
```bash
git status
# Look for "both modified:" files
```

**2. For each file, choose strategy:**

**Option A - Manual resolution (recommended for code):**
```bash
# Open file in editor
code src/file.ts

# Find conflict markers
# Keep your changes, delete markers
# Save file

git add src/file.ts
```

**Option B - Keep all your changes:**
```bash
git checkout --theirs src/file.ts
git add src/file.ts
```

**Option C - Keep all main changes:**
```bash
git checkout --ours src/file.ts
git add src/file.ts
```

**3. Continue rebase:**
```bash
git rebase --continue
```

**4. Repeat for each commit** until rebase completes

### Conflict Resolution Checklist

**For each conflict:**
- [ ] Understand what main changed (read code above `=======`)
- [ ] Understand what your branch changed (read code below `=======`)
- [ ] Decide: keep yours, keep main's, or merge both?
- [ ] Remove ALL conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`)
- [ ] Test the resolution compiles/runs
- [ ] Stage the file with `git add`
- [ ] Continue rebase with `git rebase --continue`

### Common Conflict Scenarios

#### Scenario: Import Conflicts
**Goal:** Usually keep both imports
```typescript
// Resolve by combining both
import { MainComponent } from './main';
import { YourComponent } from './yours';
```

#### Scenario: Configuration Changes
**Goal:** Usually keep your feature's config
```typescript
// Keep your feature configuration
const config = {
  feature: true,
  yourNewSetting: 'value'
};
```

#### Scenario: Dependency Version Conflicts
**Goal:** Usually keep main's version (newer/tested)
```json
// In package.json - keep main's version
"dependency": "^2.0.0"
```

#### Scenario: Test File Conflicts
**Goal:** Usually keep both tests
```typescript
// Merge both test cases
test('main test case', () => { /* ... */ });
test('your test case', () => { /* ... */ });
```

### Verification After Resolution

**After resolving each conflict:**
```bash
# Verify syntax is valid
cd src/ui && pnpm run build
cd src/api && dotnet build

# Run affected tests
pnpm test -- <test-file>
dotnet test --filter <test-name>
```

**After completing entire rebase:**
```bash
# Full verification
cd src/ui
pnpm run build
pnpm test

cd src/api
dotnet build
dotnet test
```

## Common Scenarios

### Scenario 1: Simple Rebase (No Conflicts)
```bash
# 1. Ensure clean working directory
git status

# 2. Fetch and rebase
git fetch origin main
git rebase origin/main

# 3. Force push
git push --force-with-lease
```

### Scenario 2: Rebase with Conflicts
```bash
# 1. Start rebase
git fetch origin main
git rebase origin/main

# 2. Conflicts detected - resolve them
# Edit conflicting files, then:
git add <resolved-files>
git rebase --continue

# 3. Repeat until complete
# 4. Force push
git push --force-with-lease
```

### Scenario 3: Rebase with Uncommitted Changes
```bash
# 1. Stash changes
git stash save "WIP: before rebase"

# 2. Rebase
git fetch origin main
git rebase origin/main

# 3. Restore changes
git stash pop

# 4. Resolve any conflicts from stash pop
# 5. Force push
git push --force-with-lease
```

### Scenario 4: Interactive Rebase for Cleanup
```bash
# 1. Start interactive rebase
git fetch origin main
git rebase -i origin/main

# 2. In editor, choose actions:
#    pick   = keep commit as-is
#    reword = change commit message
#    squash = combine with previous commit
#    fixup  = like squash but discard message
#    drop   = remove commit

# 3. Save and close editor
# 4. Follow prompts for each action
# 5. Force push
git push --force-with-lease
```

## Rebase vs Merge Comparison

| Aspect | Rebase | Merge |
|--------|--------|-------|
| History | Linear, clean | Shows true history with merge commits |
| Conflicts | Resolve per commit | Resolve once |
| Shared branches | ❌ Dangerous | ✅ Safe |
| Force push | Required | Not needed |
| Traceability | Harder to track when changes merged | Easy to see merge points |
| Best for | Personal feature branches | Shared branches, main branch |

## Safety Tips

### 1. Always Use `--force-with-lease`
```bash
# ✅ GOOD: Fails if remote has changes you don't have
git push --force-with-lease

# ⚠️ RISKY: Overwrites remote regardless
git push --force
```

### 2. Create Backup Branch Before Risky Rebase
```bash
# Create backup
git branch backup/feat-your-branch

# Do rebase
git rebase origin/main

# If something goes wrong:
git reset --hard backup/feat-your-branch
```

### 3. Verify After Rebase
```bash
# Run tests
pnpm test

# Check build
pnpm run build

# Review changes
git log --oneline -10
```

### 4. Communicate with Team
- Announce before rebasing shared branches (though you shouldn't!)
- Let team know if you force-pushed to a PR branch
- Consider merge instead of rebase for collaborative branches

## Troubleshooting

### Issue: "Cannot rebase: You have unstaged changes"
**Solution:**
```bash
# Option 1: Stash
git stash save "WIP"

# Option 2: Commit
git add .
git commit -m "WIP: checkpoint"
```

### Issue: "fatal: refusing to merge unrelated histories"
**Solution:**
```bash
# This usually means wrong base branch
# Verify you're rebasing onto correct branch
git fetch origin
git rebase origin/main  # Not just 'main'
```

### Issue: Too many conflicts during rebase
**Solution:**
```bash
# Abort and use merge instead
git rebase --abort
git merge origin/main
```

### Issue: Lost commits after rebase
**Solution:**
```bash
# Find lost commits in reflog
git reflog

# Reset to previous state
git reset --hard HEAD@{n}  # where n is the reflog entry
```

### Issue: Force push rejected
**Solution:**
```bash
# Fetch latest
git fetch origin

# Check if remote has changes
git log HEAD..origin/your-branch

# If safe, force push
git push --force-with-lease
```

## Integration with Repository Workflows

### Before Creating PR
```bash
# 1. Rebase onto latest main
git fetch origin main
git rebase origin/main

# 2. Run tests
cd src/ui && pnpm test

# 3. Force push
git push --force-with-lease

# 4. Create PR
```

### During PR Review
```bash
# When main has new commits:
git fetch origin main
git rebase origin/main
git push --force-with-lease

# Notify reviewers that you force-pushed
```

### After PR Approval
```bash
# Option A: Squash merge via GitHub (recommended)
# - Keeps main history clean
# - No rebase needed

# Option B: Rebase and merge
git fetch origin main
git rebase origin/main
git push --force-with-lease
# Then merge via GitHub
```

## Best Practices for This Repository

1. **Always rebase before creating PR** - Ensures clean history for review
2. **Use `--force-with-lease`** - Prevents accidental overwrites
3. **Test after rebase** - Run `pnpm test` and `pnpm run build`
4. **Keep commits atomic** - Use interactive rebase to clean up
5. **Communicate force pushes** - Let reviewers know on PR
6. **Don't rebase after PR approval** - Unless specifically requested

## Quick Reference

```bash
# Standard rebase workflow
git fetch origin main
git rebase origin/main
git push --force-with-lease

# Abort rebase
git rebase --abort

# Continue after resolving conflicts
git add <files>
git rebase --continue

# Interactive rebase
git rebase -i origin/main

# Check rebase status
git status
git log --oneline origin/main..HEAD
```

## Integration with Other Skills

- **git-worktree** - Use worktrees for parallel work during complex rebases
- See `.windsurf/workflows/stage-for-commit.md` for commit preparation
- See `.windsurf/workflows/pr-summary.md` for PR creation after rebase
