# Best Practices for Issue Organization

This reference contains quality guidelines, organizational principles, and content standards for creating well-structured issue hierarchies.

## Organizational Principles

### Hierarchy Design

**Ideal Structure:**
- **Level 1 (Epic)**: High-level initiative or major area of work
- **Level 2 (Groups)**: Thematic groupings, sub-features, or architectural concerns
- **Level 3 (Tasks)**: Individual implementation issues

**Group Size Guidelines:**
- 3-5 groups under an epic is ideal
- 2-7 tasks per group works well
- Avoid single-item groups (merge with parent or sibling)
- Avoid overly granular splits that add no value

**Grouping Strategy:**
- Group by theme, feature area, or architectural concern
- Group by technical domain (error handling, caching, authentication, etc.)
- Group by system layer (frontend, backend, database, infrastructure)
- Group by workflow stage (research, design, implementation, testing)
- Avoid arbitrary grouping just to create structure

**When to Use 2 Levels vs 3 Levels:**
- **2 levels** (Epic → Tasks): Use for smaller initiatives with <15 tasks
- **3 levels** (Epic → Groups → Tasks): Use for larger initiatives with 15+ tasks that naturally cluster into themes

### Analysis Questions

Before creating a hierarchy, answer these questions:
- Are there 3+ issues about the same feature/area?
- Can issues be grouped by architecture layer, technology, or workflow?
- Are there scattered issues that should be tracked under a common epic?
- What natural themes or concerns emerge from the issue list?
- Are there dependencies between issues that suggest grouping?

## Parent Issue Content Guidelines

### Essential Sections

Every parent/epic issue should include:
1. **Context** - Why this matters, what problem it solves, current pain points
2. **Scope** - What's in scope and explicitly what's out of scope
3. **Architectural Principles** - Design decisions, rationale, tradeoffs
4. **Implementation Guidance** - Key patterns, code examples, gotchas to avoid
5. **Testing Requirements** - Coverage expectations, critical scenarios
6. **Success Criteria** - Measurable outcomes and completion indicators
7. **References** - RFCs, documentation, related resources

### Writing Style

**Do:**
- Focus on clarity over completeness
- Provide architectural guidance and design decisions
- Include code examples for critical patterns
- Explain the "why" behind decisions
- Assume readers are capable but need direction
- Document reasoning and context comprehensively
- Link to relevant documentation/RFCs

**Don't:**
- Include emojis unless explicitly requested
- Provide full implementations (guide, don't prescribe)
- Repeat information available elsewhere
- Use vague language or hand-waving
- Assume readers have context from your analysis

### Content Depth

**Context Section:**
- 2-3 paragraphs explaining the problem and motivation
- Include current pain points and why change is needed
- Reference business or technical drivers

**Architectural Principles:**
- 3-5 key principles with rationale
- Explain tradeoffs and why specific choices were made
- Include anti-patterns to avoid

**Implementation Guidance:**
- Provide critical code patterns (not full implementations)
- Include 1-3 code examples showing the pattern
- Document gotchas, edge cases, and common mistakes
- List design decisions in a table format when helpful

**Testing Requirements:**
- Specify coverage targets (e.g., 85% minimum, 100% for critical paths)
- List 3-5 critical test scenarios
- Define integration testing expectations

## Common Organizational Patterns

### Pattern 1: Scattered Feature Issues

**Situation:** 15-30 issues about a single large feature spread across backlog

**Solution:**
- Create epic for the feature
- Group by technical concern or sub-feature
- Example groups: Error Handling, Caching, Authentication, Rate Limiting

**Example:**
```
Epic: REST API Modernization (#106)
├── Group: Error Handling (#107) - 7 tasks
├── Group: Concurrency Control (#108) - 2 tasks
├── Group: HTTP Caching (#110) - 5 tasks
└── Group: Pagination (#113) - 2 tasks
```

### Pattern 2: Test Coverage Tracking

**Situation:** Multiple issues for improving test coverage across different modules

**Solution:**
- Single parent: "Achieve 85% Test Coverage"
- Group by module, layer, or component
- Each sub-issue represents one module's coverage improvement

**Example:**
```
Epic: Achieve 85% Test Coverage (#120)
├── Task: API endpoints coverage (#121)
├── Task: Database layer coverage (#122)
├── Task: Service layer coverage (#123)
└── Task: Integration test suite (#124)
```

### Pattern 3: Migration Projects

**Situation:** Tech debt items for migrating to new architecture or technology

**Solution:**
- Migration epic with clear end state
- Group by system, layer, or phase
- Document migration strategy in epic

**Example:**
```
Epic: Migrate to async/await pattern (#130)
├── Group: Phase 1 - Core Services (#131) - 5 tasks
├── Group: Phase 2 - API Layer (#132) - 8 tasks
└── Group: Phase 3 - Background Jobs (#133) - 4 tasks
```

### Pattern 4: Observability Initiatives

**Situation:** Multiple issues for adding logging, metrics, tracing

**Solution:**
- Observability epic with architectural guidance
- Group by observability pillar (logs, metrics, traces)
- Include standards and patterns in epic

**Example:**
```
Epic: OpenTelemetry Observability (#140)
├── Group: Structured Logging (#141) - 4 tasks
├── Group: Metrics & Dashboards (#142) - 6 tasks
└── Group: Distributed Tracing (#143) - 3 tasks
```

## Workflow Efficiency

### Pre-Work
- Analyze all issues first before creating hierarchy
- Identify natural groupings and themes
- Draft epic content before creating GitHub issues
- Get node IDs for all issues upfront

### Execution Order
1. Create parent/group issues with comprehensive content
2. Query for all node IDs in batch
3. Link tasks to groups (bottom-up)
4. Link groups to epic (middle-up)
5. Verify hierarchy structure
6. Test navigation and accessibility

### Quality Checklist

Before finalizing a hierarchy, verify:
- [ ] Epic has comprehensive context and guidance
- [ ] All groups have clear themes/purposes
- [ ] Group sizes are reasonable (2-7 tasks)
- [ ] No single-item groups exist
- [ ] Issue titles are clear and descriptive
- [ ] Parent issues include code examples where helpful
- [ ] Testing requirements are specified
- [ ] Success criteria are measurable
- [ ] References link to relevant documentation
- [ ] Hierarchy is navigable in GitHub UI

## Preservation and Respect

### What NOT to Do
- Never delete existing issues
- Don't create duplicate issues
- Don't modify issue content without reason
- Don't reorganize for reorganization's sake

### What TO Do
- Preserve all original issues
- Simply reorganize into hierarchies
- Document reasoning in parent issues
- Keep original issue metadata intact

## Flexibility and Iteration

Hierarchies are not permanent. They can be reorganized as understanding evolves:
- Move sub-issues between parents as needed
- Split groups that become too large
- Merge groups that are too granular
- Adjust based on team feedback

The goal is clarity and usefulness, not perfection.

## Grep Patterns for Quick Reference

Search this file for specific guidance:
- `Ideal Structure` - Recommended hierarchy levels
- `Group Size` - Guidelines for group sizing
- `Pattern 1`, `Pattern 2`, etc. - Common organizational patterns
- `Essential Sections` - Required sections in parent issues
- `Quality Checklist` - Pre-finalization verification
