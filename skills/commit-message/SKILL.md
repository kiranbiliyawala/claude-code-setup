---
name: commit-message
description: Writes high-quality commit messages following professional tenets. This skill should be used when committing code changes, creating commits, or when the user asks for help writing commit messages. Trigger phrases include "commit", "write commit message", "create commit", "stage and commit".
---

# Commit Message Skill

Writes high-quality, high-density commit messages following professional tenets.

## Workflow

```
- [ ] Analyze staged changes (git diff --cached)
- [ ] Determine change type and scope
- [ ] Write commit message following tenets
- [ ] Execute commit
```

## Gather Context

Before writing a commit message, analyze the staged changes:

```bash
git diff --cached --name-status   # What files changed (A/M/D)
git diff --cached                  # What content changed
git log --oneline -5               # Recent commit style reference
```

For large changesets (8+ files), use parallel subagents to analyze different files.

## Commit Message Tenets

### Structure

| Element      | Requirement                                           |
| ------------ | ----------------------------------------------------- |
| Subject line | 50 chars max, capitalized, imperative mood, no period |
| Separator    | Blank line between subject and body                   |
| Body         | Natural paragraphs explaining what and why (not how)  |

### Line Wrapping

**Never manually wrap lines at column limits.** Let lines flow naturally to any length.

Bad (artificial wrapping):

```
Implements Phase 2 WebSocket architecture combining Centrifugo with RHF:
Server shadow tracks pure state, applies patches, emits snapshots for
three-way merge with local edits.
```

Good (natural paragraphs):

```
Implements Phase 2 WebSocket architecture combining Centrifugo with RHF: Server shadow tracks pure state, applies patches, emits snapshots for three-way merge with local edits.
```

### Content

| Principle           | Application                                                                 |
| ------------------- | --------------------------------------------------------------------------- |
| Conventional prefix | Use when applicable: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`     |
| Front-load keywords | Put important terms at the start of the subject                             |
| Explain the "why"   | Answer: What problem existed? Why this solution? What side effects?         |
| Be specific         | "Fix race condition in node executor" not "Fix bug"                         |
| Imperative test     | Subject should complete: "If applied, this commit will [subject]"           |
| No attribution      | Never include `Co-Authored-By`, `Signed-off-by`, or any authorship metadata |

### Examples

| Quality | Subject                                                  |
| ------- | -------------------------------------------------------- |
| Good    | "Add unique constraint to prevent duplicate claims"      |
| Bad     | "Added some database stuff"                              |
| Good    | "Refactor form validation to use progressive disclosure" |
| Bad     | "Updated forms"                                          |

## Commit Execution

After writing the message, execute the commit using a heredoc to preserve formatting:

```bash
git commit -m "$(cat <<'EOF'
Subject line here

Body paragraph explaining the change.
EOF
)"
```
