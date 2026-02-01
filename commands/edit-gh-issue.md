---
description: Edit GitHub issue body with structured workflow
argument-hint: [issue-number] [purpose]
---

Fetch issue #$1 body and apply structured edits based on purpose: $2

1. Fetch issue body to temp file: `gh issue view $1 --json body -q .body > /tmp/issue-$1-edit.md`
2. Analyze current content and enumerate specific edits needed to accomplish: $2
3. Create todo for each edit, apply sequentially using the Edit tool on `/tmp/issue-$1-edit.md`
4. Replace issue body: `gh issue edit $1 --body "$(cat /tmp/issue-$1-edit.md)"`
5. Delete `/tmp/issue-$1-edit.md`

CRITICAL - Targeted edits only:

- Use the Edit tool to make surgical changes to `/tmp/issue-$1-edit.md`
- Each edit should target a specific section, table row, or paragraph
- Rewriting the entire body risks unintended changes and is wasteful
- If you find yourself writing the full document content, STOP and use Edit instead

Recovering previous versions (if needed):

```bash
gh api graphql -f query='
{
  repository(owner: "OWNER", name: "REPO") {
    issue(number: N) {
      userContentEdits(first: 10) {
        nodes { createdAt diff }
      }
    }
  }
}' --jq '.data.repository.issue.userContentEdits.nodes[INDEX].diff'
```

Tenets for issue body:

- Clear, concise, professional
- No emoji
- Architectural guidance for implementer (they have no context of this conversation)
- Assume implementer is smart and capable
- Detailed implementation code is not required
- All required information must be in the issue body itself
