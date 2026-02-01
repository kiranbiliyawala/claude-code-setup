---
name: atomic-commits
description: Splits uncommitted changes into atomic commits using parallel subagents for analysis. This skill should be used when committing multiple unrelated changes, organizing messy work-in-progress, or when the user wants to split changes into logical commits. Trigger phrases include "atomic commits", "split commits", "organize commits", "commit separately".
---

# Atomic Commits Skill

Analyzes uncommitted changes and organizes them into logical, atomic commits. Each commit represents a single cohesive change (one feature, one fix, one refactor). Uses parallel Haiku subagents for efficient analysis and delegates commit message writing to the commit-message skill.

## Inputs/Outputs

| Input               | Description                                           |
| ------------------- | ----------------------------------------------------- |
| Uncommitted changes | Staged and unstaged modifications in the working tree |
| User preferences    | Optional guidance on how to group changes             |

| Output         | Description                                                  |
| -------------- | ------------------------------------------------------------ |
| Atomic commits | Series of well-structured commits, each with a focused scope |
| Push to remote | Changes pushed after all commits complete                    |

## Workflow

```
- [ ] Gather change summary (file list and change types)
- [ ] Launch parallel Haiku subagents to analyze and group changes
- [ ] Gather context from unchanged files and commit history
- [ ] Refine groupings based on context
- [ ] Present commit plan for user approval
- [ ] Execute commits sequentially using commit-message skill tenets
- [ ] Push to remote
```

## Step 1: Gather Change Summary

Run these commands to get the change overview (orchestrator reads only the summary, not full diffs):

```bash
git status --porcelain          # Compact file list with status codes
git diff --stat                 # Line change summary per file
git diff --cached --stat        # Staged changes summary
```

Pass this summary to subagents for detailed analysis.

## Step 2: Analyze Changes with Parallel Subagents

Launch multiple Haiku subagents in parallel. Each subagent analyzes a subset of changed files.

**Subagent prompt template:**

```
Analyze these files from a git diff and determine their logical grouping for atomic commits.

Files to analyze:
{file_list_subset}

For each file, provide:
1. What changed (brief summary)
2. Why it changed (feature/fix/refactor/docs/test/chore)
3. Suggested commit group (descriptive name)

Group related files together. A commit group should represent ONE cohesive change.
Output as JSON: {"files": [{"path": "...", "summary": "...", "type": "...", "group": "..."}]}
```

**Parallelization strategy:**

- 1-5 files: Single subagent
- 6-15 files: 2-3 subagents
- 16+ files: 4+ subagents (split evenly)

After subagents complete, merge their groupings into a preliminary commit plan.

## Step 3: Gather Context

After receiving subagent analysis, gather additional context to refine groupings.

**Orchestrator gathers summaries** (thin context):

```bash
git log --oneline -20                    # Recent commit history and style
git log --oneline --all -50 | head -30   # Branch context
```

**Launch context subagent** to examine related unchanged files:

```
Review the preliminary commit groupings and gather context from the codebase.

Preliminary groups:
{merged_subagent_output}

Changed files are in these directories:
{list_of_parent_directories}

Tasks:
1. Read key unchanged files in the same directories (imports, exports, related functions)
2. Check if changes span a single feature/refactor that should stay together
3. Check if changes touch unrelated subsystems that should be split
4. Review recent commits for similar changes to inform grouping

Output refined groupings with rationale:
{"groups": [{"name": "...", "files": [...], "rationale": "..."}]}
```

**Context signals to look for:**

| Signal | Implication |
|--------|-------------|
| Files share imports/exports | Likely same commit |
| Files in different subsystems | Likely separate commits |
| Recent commit touched same files together | Follow that pattern |
| Test file + implementation file | Same commit |
| Config change + code change | Usually separate commits |

## Step 4: Present Commit Plan

Before executing, present the plan to the user:

```markdown
## Proposed Atomic Commits

### Commit 1: [Group Name]

- `path/to/file1.ts` - [brief change]
- `path/to/file2.ts` - [brief change]

### Commit 2: [Group Name]

- `path/to/file3.py` - [brief change]

...
```

Proceed immediately to execution without waiting for user approval.

## Step 5: Execute Commits

For each commit group, in order:

1. **Stage files** (entire files, no partials):

   ```bash
   git add path/to/file1 path/to/file2
   ```

2. **Write commit message** following commit-message skill tenets:
   - Subject: 50 chars max, capitalized, imperative mood, no period
   - Prefix: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`
   - Body: Natural paragraphs explaining what and why (not how)
   - No manual line wrapping
   - No attribution metadata

3. **Execute commit**:

   ```bash
   git commit -m "$(cat <<'EOF'
   Subject line here

   Body paragraph explaining the change.
   EOF
   )"
   ```

4. **Verify** commit succeeded before proceeding to next group.

## Step 6: Push to Remote

After all commits complete:

```bash
git push
```

If push fails (e.g., remote has new commits), inform user and suggest:

- `git pull --rebase` then retry push
- Or manual resolution

## Error Handling

| Error                  | Action                                      |
| ---------------------- | ------------------------------------------- |
| No uncommitted changes | Report "Nothing to commit" and exit         |
| Commit fails (hooks)   | Show error, do not proceed to next commit   |
| Push rejected          | Report rejection reason, suggest resolution |
| Merge conflicts        | Stop and inform user, do not auto-resolve   |

## Example Session

```
User: /atomic-commits
```
