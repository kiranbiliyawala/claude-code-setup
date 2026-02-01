# Issue Writing Tenets

These tenets guide the creation of high-quality GitHub issues.

## Core Principles

1. **Clear, concise, professional** - Write for busy developers scanning issues
2. **No emoji** - Maintain professional tone
3. **Include the "why"** - Motivation helps implementers make good tradeoff decisions
4. **Architectural guidance without prescriptive code** - Point to patterns, not implementations
5. **Assume implementer is smart and capable** - Don't over-explain obvious things
6. **Include acceptance criteria** - How does the implementer know they're done?
7. **State what's out of scope** - Prevents scope creep and clarifies boundaries
8. **Self-contained** - No "as discussed" references; all context in the issue body
9. **Link to relevant existing code/docs** - Give starting points, not prescriptions

## Issue Body Structure

```markdown
## Summary

[1-2 sentences: What needs to be done and why]

## Context

[Why this is needed. Business motivation, technical debt being addressed, or user problem being solved. Skip if obvious from summary.]

## Approach

[Architectural guidance. Which components/files are involved? What patterns to follow? What tradeoffs to consider?]

## Acceptance Criteria

- [ ] [Specific, testable criterion]
- [ ] [Another criterion]
- [ ] [Include test requirements if applicable]

## Out of Scope

- [What this issue explicitly does NOT include]
- [Prevents scope creep]

## References

- [Link to relevant code: `src/path/to/file.py`]
- [Link to relevant docs or ADRs]
```

## Section Guidelines

### Summary
- One or two sentences maximum
- State the what and the why
- Should be understandable without reading further

### Context
- Explain motivation, not implementation
- Include relevant background that isn't obvious
- Skip entirely if the summary is self-explanatory

### Approach
- Provide architectural direction
- Reference existing patterns in the codebase
- Mention files/modules that will likely be involved
- Do NOT write implementation code
- Do NOT dictate exact solutions

### Acceptance Criteria
- Must be specific and testable
- Use checkbox format for tracking
- Include test requirements when applicable
- Each criterion should be independently verifiable

### Out of Scope
- Explicitly list related work not included
- Helps prevent scope creep during implementation
- Can be brief; even one item helps

### References
- Link to relevant source files using relative paths
- Link to relevant documentation or ADRs
- Link to related issues if applicable
