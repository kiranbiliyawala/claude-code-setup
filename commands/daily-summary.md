---
description: Generate a CTO-friendly daily summary of commits and issues, copy to clipboard in WhatsApp format
allowed-tools: Bash(gh:*), Bash(git log:*), Bash(echo:*), Bash(pbcopy:*), Bash(cat:*), Read, Grep, Glob
---

# Daily Work Summary Generator

Generate a concise, CTO-friendly summary of today's work and copy it to clipboard in WhatsApp format.

**CRITICAL**: You MUST read ALL content in full before writing the summary. Commit subject lines and issue titles are insufficient - they compress hours of work into a few words. The full context is in the bodies.

## Step 1: Gather Raw Data

Use the GitHub CLI and git to collect lists:

1. **Get repo info**:
   ```
   gh repo view --json owner,name --jq '.owner.login + "/" + .name'
   ```

2. **Issues updated today** (just the list):
   ```
   gh issue list --state all --search "updated:>=$(date +%Y-%m-%d)" --limit 50
   ```

3. **Commits made today** (just hashes and subjects for now):
   ```
   git log --since="$(date +%Y-%m-%d)T00:00:00" --until="$(date -v+1d +%Y-%m-%d)T00:00:00" --all --format="%h %s" --no-merges
   ```

## Step 2: Read FULL Content (MANDATORY)

**Do NOT skip this step. Do NOT summarize from titles/subjects alone.**

1. **Read FULL commit messages** - the body explains WHY and WHAT changed:
   ```
   git log --since="$(date +%Y-%m-%d)T00:00:00" --until="$(date -v+1d +%Y-%m-%d)T00:00:00" --all --no-merges --format="=== COMMIT %h ===%n%B"
   ```

2. **Read FULL issue bodies** for each issue found in Step 1:
   ```
   gh issue view N --json body,title,createdAt,state --jq '"### Issue N: \(.title)\nState: \(.state)\nCreated: \(.createdAt)\n\n\(.body)"'
   ```

3. **For issues that existed before today**: Check what changed via GraphQL:
   ```
   gh api graphql -f query='{ repository(owner: "OWNER", name: "REPO") { issue(number: N) { createdAt userContentEdits(first: 5) { nodes { createdAt diff } } } } }'
   ```

**Why this matters**: A commit subject like "fix(forms): Handle array wildcards" hides 30+ lines explaining the actual bug, root cause, and solution. An issue title like "Implement pull-model authentication" hides a 7-phase implementation plan with 73 tests.

## Step 3: Analyze with Full Context

Now that you have the full picture:

- Group commits by theme/feature (conventional commit prefixes help)
- Understand the SCOPE of each change from the full commit body
- Identify issues CLOSED vs CREATED today
- Note major architectural changes, security improvements, lines removed/added
- Focus on OUTCOMES and VALUE, not just "what files changed"

## Step 4: Write Summary

Write a summary that:

- Is under 50 words total (excluding date and bullets)
- Uses high-level business language (no PR/issue numbers in the WhatsApp output)
- Accurately reflects the SCALE of work (don't undersell major refactors)
- A CTO would find meaningful
- **Professional and neutral tone** - factual accomplishments, no fluff

## Step 5: Format for WhatsApp and Copy

Format using WhatsApp syntax:

- Bold: `*text*`
- Bullet points: `•` character

Structure:

```
*DD/MM/YY*

• First accomplishment
• Second accomplishment
• Third accomplishment
• Fourth accomplishment (if needed)
```

Copy to clipboard using:

```bash
cat << 'EOF' | pbcopy
*DD/MM/YY*

• First accomplishment
• ...
EOF
```

## Step 6: Confirm

Show the user exactly what was copied to clipboard.
