---
name: create-issue
description: Create high-quality GitHub issues using the gh CLI. This skill should be used when the user asks to create a GitHub issue, write an issue for a task, or convert a task description into an issue. It generates well-structured issue bodies following professional writing tenets and uses `gh issue create` for submission.
---

# Create Issue

## Overview

This skill creates high-quality GitHub issues from task descriptions. It generates professional, self-contained issue bodies that provide architectural guidance without prescriptive implementation details, then submits them via the `gh` CLI.

## Workflow

### 1. Gather Task Information

Obtain the task description from:
- Skill arguments (if provided)
- Current conversation context
- User clarification (if needed)

Identify relevant context:
- Which files/modules are involved
- Related documentation or ADRs
- Existing patterns in the codebase

### 2. Generate Issue Body

Read `references/tenets.md` for issue writing guidelines, then draft the issue body following this structure:

```markdown
## Summary

[1-2 sentences: What needs to be done and why]

## Context

[Why this is needed - skip if obvious from summary]

## Approach

[Architectural guidance, relevant files/patterns, tradeoffs]

## Acceptance Criteria

- [ ] [Specific, testable criteria]

## Out of Scope

- [What this issue does NOT include]

## References

- [Links to relevant code and docs]
```

### 3. Write to Temp File

Write the issue body to a temporary file:

```bash
cat > /tmp/issue-body.md << 'EOF'
[generated issue body]
EOF
```

### 4. Create Issue via gh CLI

Execute gh issue create with the generated body:

```bash
gh issue create --title "[issue title]" --body-file /tmp/issue-body.md [options]
```

Common options:
- `--label bug,enhancement` - Add labels
- `--assignee @me` - Self-assign
- `--assignee username` - Assign to specific user
- `--milestone "v1.0"` - Add to milestone
- `--project "Board Name"` - Add to project (requires `gh auth refresh -s project`)

### 5. Report Result

Return the created issue URL to the user.

## Quality Checklist

Before creating the issue, verify:

- [ ] Title is concise and actionable (imperative mood)
- [ ] Summary explains what and why in 1-2 sentences
- [ ] Approach provides direction without dictating implementation
- [ ] Acceptance criteria are specific and testable
- [ ] Out of scope is defined (even if brief)
- [ ] No emoji anywhere in the issue
- [ ] No "as discussed" or external references
- [ ] Relevant code paths are linked
- [ ] Implementer can work from this issue alone

## Examples

**User request:** "Create an issue for adding retry logic to the API client"

**Generated issue:**

```markdown
## Summary

Add exponential backoff retry logic to the API client for transient failures.

## Context

The API client currently fails immediately on network errors or 5xx responses. This causes unnecessary failures during brief outages or rate limiting.

## Approach

Extend the existing `ApiClient` class in `src/client/api.py`. Consider:
- Retry on 5xx status codes and connection errors
- Exponential backoff with jitter to avoid thundering herd
- Configurable max retries and base delay
- Follow the retry pattern used in `src/client/auth.py:45-60`

## Acceptance Criteria

- [ ] Retries on 5xx responses and connection errors
- [ ] Exponential backoff with configurable base delay
- [ ] Maximum retry count is configurable (default: 3)
- [ ] Logs retry attempts at DEBUG level
- [ ] Unit tests cover retry scenarios

## Out of Scope

- Retry on 4xx errors (client errors should fail fast)
- Circuit breaker pattern (separate issue)

## References

- `src/client/api.py` - Main API client
- `src/client/auth.py:45-60` - Existing retry pattern
```

**Command executed:**

```bash
gh issue create --title "Add retry logic to API client" --body-file /tmp/issue-body.md --label enhancement
```

## References

- `references/tenets.md` - Issue writing tenets and guidelines
