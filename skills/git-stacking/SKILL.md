---
name: git-stacking
description: Git-branchless stacking commands for managing stacked commits and branches. This skill should be used when working with git-branchless tools (git move, git restack, git sync, git submit), managing stacked PRs, rebasing commit stacks, fixing abandoned commits, or pushing stacked branches to remote. Trigger phrases include "move stack", "restack", "sync branches", "submit PRs", "stacked commits", "abandoned commits", or any git-branchless workflow questions.
---

# Git Stacking with git-branchless

## Overview

Guide for managing stacked commits and branches using git-branchless. Covers the core commands (`git move`, `git restack`, `git sync`, `git submit`) and when to use each one.

## Decision Tree

To determine which command to use:

```
What's the situation?
│
├─ Adding a NEW commit to base of stack?
│  └─ git move -s <first-stacked-branch>
│
├─ Commits show "rewritten as X" in smartlog?
│  └─ git restack
│
├─ Main branch updated, need to rebase stack?
│  └─ git sync --pull
│
├─ Need to push stack to remote?
│  └─ git submit --create
│
├─ git submit fails with "non-fast-forward"?
│  └─ Set upstream tracking (see Troubleshooting section)
│
├─ Need to insert commit between others?
│  └─ git move -I -x <commit> -d <destination>
│
└─ Need to move entire branch to new location?
   └─ git move -b <branch> -d <destination>
```

## Core Commands

### Adding a Commit to Base of Stack

After making a new commit on a base branch, move the stacked branches onto it:

```bash
git add <files>
git commit -m "message"
git move -s <first-stacked-branch>
```

The `-d` flag defaults to HEAD, so typically omit it.

### Fixing Stale Branch Pointers

When smartlog shows commits marked "rewritten as X", branch pointers are stale:

```bash
git restack
```

This reattaches abandoned children to their rewritten parents and updates branch pointers.

### Syncing with Main

To rebase all local stacks onto updated main branch:

```bash
git sync --pull      # Fetch main first, then rebase
git sync --merge     # Also resolve conflicts
```

### Pushing Stack to Remote

```bash
git submit --create  # Push and create branches that don't exist
git submit           # Push only branches that already exist on remote
```

Prerequisites:
- `git config remote.pushDefault origin`
- Branches must have upstream tracking set (see Troubleshooting below)

### Troubleshooting: git submit Fails with Non-Fast-Forward

If `git submit` fails after `restack` with errors like:
```
! [rejected] issue-64 -> issue-64 (non-fast-forward)
```

**Cause:** Branches lack upstream tracking. Without tracking, `git submit` uses `--set-upstream` (non-force) instead of force-pushing.

**Diagnosis:**
```bash
git branch -vv | grep issue-
```
Branches without `[origin/...]` shown lack tracking.

**Fix:** Set tracking for all stack branches:
```bash
for b in $(git branchless query -b 'branches() & stack()'); do
  git branch --set-upstream-to=origin/$b $b
done
```

**Alternative:** Use force-push wrapper that works regardless of tracking:
```bash
git fetch origin --prune
git push --force-with-lease --atomic origin $(git branchless query -b 'branches() & stack()')
```

### Inserting a Commit

To insert a commit between existing commits:

```bash
git move -I -x <commit> -d <destination>
```

Flags: `-I` (insert mode), `-x` (exact - only this commit, not descendants).

## Key Flag Reference

| Flag | Command | Meaning |
|------|---------|---------|
| `-s` | move | Source: move this commit + descendants |
| `-b` | move | Base: move entire branch from fork point |
| `-d` | move | Destination (defaults to HEAD) |
| `-x` | move | Exact: only this commit, not descendants |
| `-I` | move | Insert mode |
| `--merge` | move/sync | Resolve conflicts |
| `--create` | submit | Create new remote branches |
| `--pull` | sync | Fetch main before syncing |

## `-s` vs `-b` Explained

Given this structure:
```
◇ main
● A (fork point)
● B
● C (branch tip)
```

- `git move -s C -d main` → moves only C
- `git move -b C -d main` → moves A, B, and C (entire line of work)

Think of `-b` as "branch" - it moves everything from the fork point.

## Common Revset Expressions

Use with commands that accept revsets (e.g., `git submit 'expr'`):

| Expression | Meaning |
|------------|---------|
| `stack()` | All draft commits in current stack |
| `branches()` | Commits with branch pointers |
| `draft()` | All unpublished commits |
| `children(x)` | Immediate children of x |
| `descendants(x)` | x and all commits built on it |

Operators: `+` (union), `&` (intersection), `:x` (ancestors), `x:` (descendants).

## Detailed Reference

For complete flag documentation, examples, and edge cases, see `references/commands.md`.
