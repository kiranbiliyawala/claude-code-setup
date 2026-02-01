# Git-Branchless Command Reference

## git move

Relocates commits within the repository's commit graph. Operates in-memory by default (doesn't touch working copy).

### Flags

| Flag | Long Form | Description |
|------|-----------|-------------|
| `-s` | `--source` | Move this commit and all descendants |
| `-b` | `--base` | Move entire branch from merge-base (fork point) |
| `-d` | `--dest` | Destination commit (defaults to HEAD) |
| `-x` | `--exact` | Move only specified commit, not descendants |
| `-I` | `--insert` | Insert commit after destination |
| `-F` | `--fixup` | Combine commits into destination (like rebase fixup) |
| | `--merge` | Enable merge conflict resolution |
| | `--in-memory` | Force in-memory rebase |

### Default Behavior

`git move` with no flags defaults to `--base HEAD` (moves current stack).

### Examples

**Move stack onto new HEAD:**
```bash
git move -s feature-branch
```

**Move entire line of work:**
```bash
git move -b feature-branch -d main
```

**Insert single commit:**
```bash
git move -I -x abc123 -d def456
```

**Move with conflict resolution:**
```bash
git move -s feature-branch --merge
```

### -s vs -b Visual

```
◇ main
● A (fork point / merge-base)
● B
● C (feature-branch points here)
```

| Command | What Moves |
|---------|------------|
| `git move -s C -d main` | Only C |
| `git move -b C -d main` | A, B, and C |

The `-b` flag calculates the merge-base between source and destination, then moves all commits from that point.

---

## git restack

Fixes "abandoned commits" that result from rewrite operations (amend, rebase).

### When to Use

When smartlog shows commits with `✕` icon and "rewritten as X" messages:
```
| x 3c36a1e (rewritten as d7f701e8)
| % e208dc1 (rewritten as cdf624be) (> issue-63)
```

### Usage

```bash
git restack              # Fix all abandoned commits
git restack <commit>     # Fix only children of specific commit
```

### What It Does

1. Identifies commits whose parents were rewritten
2. Rebases abandoned commits onto the rewritten parent versions
3. Updates branch pointers to follow the moved commits

### Not For

- Rebasing onto updated main branch (use `git sync`)
- Moving commits to new location (use `git move`)

---

## git sync

Rebases all local commit stacks onto the main branch without checking them out individually.

### Flags

| Flag | Description |
|------|-------------|
| `--pull` | Fetch main from remote first (like `git pull`) |
| `--merge` | Resolve merge conflicts for all conflicting stacks |

### Usage

```bash
git sync              # Rebase onto local main (idempotent)
git sync --pull       # Fetch main, then rebase all stacks
git sync --merge      # Also resolve conflicts
```

### Conflict Handling

By default, `git sync` skips conflicting stacks and prints a summary. To resolve:

```bash
git sync --merge                                    # All stacks
git move -b <commit> -d origin/main --merge         # Single stack
```

### vs git restack

| Command | Purpose |
|---------|---------|
| `git restack` | Repair graph after local rewrites (amend) |
| `git sync` | Update all stacks relative to upstream main |

---

## git submit

Pushes multiple branches to remote simultaneously.

### Flags

| Flag | Description |
|------|-------------|
| `-c`, `--create` | Push new branches that don't exist on remote |
| `-F`, `--forge` | Force specific forge: `branch`, `github`, `phabricator` |
| `--dry-run` | Report what would be submitted without doing it |
| `--jobs N` | Parallelism for pushing |

### Usage

```bash
git submit              # Force-push existing remote branches
git submit --create     # Also create new branches
git submit '@'          # Submit current commit's branches only
git submit 'draft()'    # Submit all draft branches
git submit -F branch    # Force branch forge (avoids buggy github forge)
```

### Prerequisites

1. Set default push remote:
   ```bash
   git config remote.pushDefault origin
   ```

2. Branches must have upstream tracking configured (critical for force-push):
   ```bash
   git branch -vv  # Check tracking status
   ```

### Troubleshooting: Non-Fast-Forward Rejections

**Symptom:** After `git restack`, `git submit --create` fails:
```
! [rejected] issue-64 -> issue-64 (non-fast-forward)
```

**Root cause:** Branches without upstream tracking are treated as "new branches to create" and pushed with `--set-upstream` (non-force) instead of force-pushed.

**Diagnosis:**
```bash
git branch -vv | grep -v '\[origin/'  # Show branches without tracking
```

**Solution 1:** Set tracking for all stack branches:
```bash
for b in $(git branchless query -b 'branches() & stack()'); do
  git branch --set-upstream-to=origin/$b $b 2>/dev/null || true
done
```

**Solution 2:** Use force-push wrapper (works regardless of tracking):
```bash
git fetch origin --prune
git push --force-with-lease --atomic origin $(git branchless query -b 'branches() & stack()')
```

**Prevention:** After first push of new branches, tracking is automatically set. Issue only occurs when branches exist on remote but local tracking was never established.

### Warning

Force-pushes by default. Only use on branches under review that others aren't actively using.

### Forge Note

The `github` forge is marked "likely buggy" in git-branchless docs. If you encounter issues, force the simpler `branch` forge with `-F branch`.

---

## git sl (smartlog)

Visualizes the commit graph with branch information.

### Reading the Output

| Symbol | Meaning |
|--------|---------|
| `●` | Visible commit |
| `◯` | Commit in stack |
| `◇` | Public commit (main) |
| `✕` | Abandoned commit (needs restack) |
| `%` | Commit with dirty working copy |
| `>` | Current HEAD |

### Rewritten Commits

When you see:
```
| x abc123 (rewritten as def456)
```

This commit was rewritten (amend/rebase) but descendants weren't updated. Run `git restack`.

---

## Revset Reference

### Core Functions

| Function | Description |
|----------|-------------|
| `all()` | All visible commits |
| `none()` | Empty set |
| `stack([x])` | Draft commits in stack containing x (or HEAD) |
| `branches([pattern])` | Commits with branch pointers |
| `draft()` | All unpublished commits |
| `public()` | All public commits |
| `main()` | Main branch commit |

### Navigation Functions

| Function | Description |
|----------|-------------|
| `ancestors(x)` | x and all ancestors |
| `descendants(x)` | x and all descendants |
| `parents(x)` | Immediate parents |
| `children(x)` | Immediate children |
| `parents.nth(x, n)` | nth parent |
| `ancestors.nth(x, n)` | nth generation ancestor |

### Filtering Functions

| Function | Description |
|----------|-------------|
| `message(pattern)` | Commits matching message |
| `author.name(pattern)` | By author name |
| `author.email(pattern)` | By author email |
| `paths.changed(path)` | Commits touching path |
| `merges()` | Merge commits only |
| `current(x)` | Current versions after rewrites |
| `exactly(x, n)` | x only if contains exactly n commits |

### Operators

| Operator | Meaning |
|----------|---------|
| `x + y`, `x \| y`, `x or y` | Union |
| `x & y`, `x and y` | Intersection |
| `x - y` | Difference |
| `x % y` | Only (ancestors of x, not ancestors of y) |
| `:x`, `::x` | Ancestors |
| `x:`, `x::` | Descendants |
| `x:y`, `x::y` | Range (descendants of x AND ancestors of y) |

### Examples

```bash
git submit 'draft() & branches()'     # All draft branches
git query 'stack() & paths.changed(src/)'  # Stack commits touching src/
git test run --exec 'pytest' 'branches()'  # Test all branches
```

---

## Other Useful Commands

| Command | Description |
|---------|-------------|
| `git next` | Move to next commit in stack |
| `git prev` | Move to previous commit in stack |
| `git amend` | Amend current commit |
| `git query <revset>` | Print commits matching revset |
| `git test` | Run tests on commits |

---

## Sources

- [git move wiki](https://github.com/arxanas/git-branchless/wiki/Command:-git-move)
- [git restack wiki](https://github.com/arxanas/git-branchless/wiki/Command:-git-restack)
- [git sync wiki](https://github.com/arxanas/git-branchless/wiki/Command:-git-sync)
- [git submit wiki](https://github.com/arxanas/git-branchless/wiki/Command:-git-submit)
- [Revsets reference](https://github.com/arxanas/git-branchless/wiki/Reference:-Revsets)
- [Tutorial](https://github.com/arxanas/git-branchless/wiki/Tutorial)
