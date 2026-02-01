# ADR Template

Use this template when creating new Architecture Decision Records.

---

```markdown
# ADR-NNNN: <Title>

## Status

Proposed | Accepted | Deprecated | Superseded by [ADR-XXXX](./XXXX-title.md)

## Date

YYYY-MM-DD

## Context

<!--
Describe the situation that requires a decision. Include:
- What problem or need exists?
- What is the current state?
- Why is a decision needed now?
- What constraints exist?

Write 2-4 paragraphs. Be factual and objective.
-->

## Decision Drivers

<!--
List the key factors influencing this decision as bullets:
- Performance requirements
- Team expertise
- Existing infrastructure
- Cost constraints
- Timeline pressures
- Maintainability needs
-->

- Driver 1
- Driver 2
- Driver 3

## Considered Options

### Option 1: <Name>

<!-- Brief description of the option -->

Pros:
- Pro 1
- Pro 2

Cons:
- Con 1
- Con 2

### Option 2: <Name>

<!-- Brief description of the option -->

Pros:
- Pro 1
- Pro 2

Cons:
- Con 1
- Con 2

### Option 3: <Name> (Selected)

<!-- Mark the selected option in the heading -->

Pros:
- Pro 1
- Pro 2

Cons:
- Con 1
- Con 2

## Decision

<!--
State the decision clearly and concisely. Use active voice.
Example: "Use PostgreSQL as the primary database for user data."

If applicable, include a summary table showing responsibilities or mappings.
-->

## Rationale

<!--
Explain WHY this option was selected. Include:
- How it addresses the decision drivers
- Evidence supporting the choice (benchmarks, research, prior experience)
- Why alternatives were rejected
- Any assumptions made

This section provides the deeper reasoning that Context and Decision summarize.
-->

## Consequences

### Positive

- Consequence 1
- Consequence 2

### Negative

- Consequence 1
- Consequence 2

### Risks

- Risk 1: Mitigation strategy
- Risk 2: Mitigation strategy

## Related Decisions

<!-- Link to related ADRs that influence or are influenced by this decision -->

- [ADR-XXXX](./XXXX-title.md): Brief description of relationship
```

---

## Section Guidelines

| Section           | Length    | Focus                                    |
| ----------------- | --------- | ---------------------------------------- |
| Context           | 2-4 para  | Problem statement, constraints           |
| Decision Drivers  | 3-7 items | Key factors, requirements                |
| Considered Options| 2-4 opts  | Pros/cons for each, mark selected        |
| Decision          | 1-3 para  | What was decided, possibly with table    |
| Rationale         | 2-5 para  | Why this choice, evidence                |
| Consequences      | 3-6 items | Positive, negative, risks with mitigations|

## Writing Style

- **Clear** - Unambiguous language, no jargon without definition
- **Crisp** - Concise sentences, no filler words or redundancy
- **Professionally neutral** - Objective tone, no advocacy or persuasion
- **No emoji** - Plain text only

## Quality Checklist

- [ ] Single decision per ADR (split if needed)
- [ ] Trade-offs explicitly documented
- [ ] Consequences include both positive AND negative
- [ ] Risks include mitigation strategies
- [ ] Related ADRs linked bidirectionally
- [ ] Status reflects current state
- [ ] Date is accurate
- [ ] Writing is clear, crisp, neutral, no emoji
