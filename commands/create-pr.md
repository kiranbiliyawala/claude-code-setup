---
description: Create PR with comprehensive description from commit history
argument-hint: <base-branch>
allowed-tools: Bash, Read, Grep, Glob
---

# Create Pull Request with High-Quality Description

You are tasked with creating a GitHub pull request from the current branch into $1 (base branch) with a comprehensive, well-structured description.

## Step 0: Get Current Branch

First, determine the current branch:

```bash
git branch --show-current
```

Store this as the compare branch for use in subsequent commands.

## Step 1: Gather Commit Information

Retrieve all commit messages and their full details between the base branch and current branch using:

```bash
git log <base-branch>..<current-branch> --format=fuller
```

Read through ALL commits carefully to understand the full scope of changes.

## Step 2: Analyze the Changes

Examine the actual code changes to understand what was modified:

```bash
git diff <base-branch>...<current-branch> --stat
```

If needed, look at specific file changes to understand implementation details.

## Step 3: Craft the PR Description

Based on the commit messages and code changes, create a comprehensive PR description following this structure:

```markdown
## What?

[Provide a clear, concise summary of what changes are included in this PR]

## Why?

[Explain the problem being solved, the business/technical rationale, and why these changes matter]

## How?

[Highlight key design decisions, implementation approaches, and important technical details]

## Testing?

[Describe how the changes were validated, test coverage, and steps to verify the functionality]

## Related Issues

[Link any related issues, tickets, or PRs using #issue-number or full URLs]

## Additional Notes

[Optional: Known limitations, follow-up work needed, areas requiring special review attention]
```

## Guidelines for Writing the Description

- **Be specific**: Don't just list commit messages. Synthesize them into a coherent narrative
- **Explain the "why"**: Connect technical decisions to their purpose
- **Include implementation details**: Mention specific approaches, libraries, or patterns used
- **Be thorough but concise**: Provide complete context without overwhelming the reader
- **Use bullet points**: For clarity when listing multiple items
- **NO EMOJIS**: Keep the tone professional and straightforward

## Step 4: Create the Pull Request

Create the PR using one of these approaches:

**Option A (recommended)**: Using heredoc with --body

```bash
gh pr create --base <base-branch> --head <current-branch> --title "[Your Title]" --body "$(cat <<'EOF'
[Your generated description here]
EOF
)"
```

**Option B**: Using --body-file with stdin

```bash
echo "[Your generated description]" | gh pr create --base <base-branch> --head <current-branch> --title "[Your Title]" --body-file -
```

Note: The `--head` flag can be omitted if you're already on the current branch, as gh will use it by default.

## Important Notes

- Examine ALL commits, not just the most recent one
- Look at actual code changes to verify what the commits claim to do
- If commits reference issue numbers, include them in the "Related Issues" section
- If you find test-related commits, highlight them in the "Testing?" section
- Group related commits together when explaining the changes
