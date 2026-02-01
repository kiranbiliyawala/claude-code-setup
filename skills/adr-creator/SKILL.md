---
name: adr-creator
description: Create Architecture Decision Records (ADRs) following best practices. This skill should be used when the user asks to create, document, or record an architectural decision, or when discussing significant technical choices that warrant documentation. Trigger phrases include "create an ADR", "document this decision", "record this architecture choice", or explicit /adr invocation.
---

# ADR Creator

Create Architecture Decision Records following the Nygard template with extended sections for decision drivers, options analysis, and consequences.

## When to Use This Skill

- User explicitly requests an ADR with `/adr` or "create an ADR"
- Discussing a significant architectural decision that should be documented
- Comparing multiple technical approaches for a problem
- Making technology, tool, or pattern selections

## Writing Style

All ADR content must follow these tenets:

- **Clear** - Unambiguous language, no jargon without definition
- **Crisp** - Concise sentences, no filler words or redundancy
- **Professionally neutral** - Objective tone, no advocacy or persuasion
- **No emoji** - Plain text only

## Workflow

### Step 1: Gather Context

Before writing an ADR, collect information about:

1. **The problem or need** - What situation requires a decision?
2. **Constraints and drivers** - What factors influence the choice?
3. **Options considered** - What alternatives exist? (minimum 2-3)
4. **Trade-offs** - What are the pros/cons of each option?

If information is missing, ask the user targeted questions.

### Step 2: Determine Next ADR Number

Run the numbering script to get the next available ADR number:

```bash
python ~/.claude/skills/adr-creator/scripts/next_adr_number.py <adr-directory>
```

Default directory: `docs/architecture/decisions/`

### Step 3: Write the ADR

Create the ADR file at: `docs/architecture/decisions/NNNN-<kebab-case-title>.md`

Follow the template structure in `references/adr-template.md`:

| Section             | Purpose                                           |
| ------------------- | ------------------------------------------------- |
| Title               | `ADR-NNNN: <Descriptive Title>`                   |
| Status              | Proposed, Accepted, Deprecated, or Superseded     |
| Date                | YYYY-MM-DD format                                 |
| Context             | Why this decision is needed (2-4 paragraphs)      |
| Decision Drivers    | Bulleted list of key factors                      |
| Considered Options  | 2-3+ options with pros/cons for each              |
| Decision            | What was decided and why                          |
| Rationale           | Deeper explanation with evidence                  |
| Consequences        | Positive, Negative, and Risks subsections         |
| Related Decisions   | Links to related ADRs                             |

### Step 4: Validate Quality

Ensure the ADR:

- Focuses on a single decision (split if multiple)
- Documents trade-offs explicitly (do not hide consequences)
- Is concise and factual (avoid design guide territory)
- Includes concrete evidence in Rationale when possible

## Status Transitions

| From       | To         | When                                        |
| ---------- | ---------- | ------------------------------------------- |
| (new)      | Proposed   | Initial creation, pending team review       |
| Proposed   | Accepted   | Team approves the decision                  |
| Accepted   | Deprecated | Decision no longer applies                  |
| Accepted   | Superseded | Replaced by a new ADR (link to replacement) |

When superseding an ADR, update the old ADR's status to include: `Superseded by [ADR-NNNN](./NNNN-title.md)`

## Resources

### scripts/next_adr_number.py

Scans a directory for existing ADRs and returns the next available number. Handles gaps in numbering.

### references/adr-template.md

Complete ADR template following the extended Nygard format with all sections pre-filled with guidance comments.
