---
name: github-issue-organizer
description: Analyzes and reorganizes GitHub issues into hierarchical sub-issue structures using GraphQL API. This skill should be used when consolidating fragmented issues, creating epics, grouping related issues, or organizing project backlogs.
version: 2.0.0
---

# GitHub Issue Organizer

Analyze and reorganize GitHub issues into hierarchical structures using GitHub's sub-issues feature (released January 2025).

## Purpose

Transform scattered GitHub issues into well-organized epics with clear hierarchies. This enables better project tracking, clearer roadmaps, and improved developer experience through structured work organization.

## When to Use This Skill

Activate this skill to:
- Consolidate fragmented or scattered GitHub issues into epics
- Create parent/epic issues to organize related work
- Reorganize flat issue lists into hierarchical structures
- Group issues by theme, feature area, architectural concern, or project phase
- Analyze existing issues and recommend organizational improvements

## Core Workflow

### Phase 1: Analysis

Gather and analyze existing issues to identify organizational opportunities.

**Steps:**
1. Fetch all issues from the repository:
   ```bash
   gh issue list --repo OWNER/REPO --limit 1000 --state all --json number,title,state,labels
   ```

2. Identify patterns by asking:
   - Are there 3+ issues about the same feature/area?
   - Can issues be grouped by architecture layer, technology, or workflow?
   - What natural themes or concerns emerge?
   - Are there dependencies suggesting grouping?

3. Review `references/best-practices.md` for organizational patterns (grep: `Pattern 1`, `Pattern 2`)

**Output:** Clear understanding of how issues should be grouped.

### Phase 2: Design Hierarchy

Design a multi-level structure that makes sense for the issue set.

**Recommended Structure:**
- **Level 1 (Epic)**: High-level initiative
- **Level 2 (Groups)**: Thematic groupings or sub-features (3-5 groups ideal)
- **Level 3 (Tasks)**: Individual implementation issues (2-7 per group)

**Design Principles:**
- Group by technical concern, feature area, or system layer
- Keep group sizes reasonable (not too granular, not too broad)
- Preserve all original issues (reorganize, don't delete)

Consult `references/best-practices.md` for detailed guidance (grep: `Hierarchy Design`, `Grouping Strategy`).

### Phase 3: Create Parent Issues

Create comprehensive parent/epic issues that provide architectural guidance and context.

**Essential Content:**
Use `templates/parent-issue-template.md` as the starting structure. Every parent issue should include:
- Context explaining why this matters
- Clear scope boundaries (in/out of scope)
- Architectural principles with rationale
- Implementation guidance with code examples
- Testing requirements
- Success criteria
- References to relevant documentation

**Content Guidelines:**
- Focus on design decisions and "why", not full implementations
- Provide architectural guidance, not prescriptive code
- Include code examples for critical patterns only
- Assume readers are capable but need direction
- No emojis unless explicitly requested

For detailed quality standards, see `references/best-practices.md` (grep: `Parent Issue Content`, `Writing Style`).

### Phase 4: Build Hierarchy with GraphQL

Execute the organizational plan using GitHub's GraphQL API.

**Step 4.1 - Get Node IDs:**

GraphQL mutations require node IDs, not issue numbers. Query for all IDs upfront:

```bash
# Use the helper script for batch queries
scripts/get-node-ids.sh OWNER REPO "106 107 108 48 55 62"
```

Or construct GraphQL query manually (see `references/graphql-api.md`, grep: `Batch Query`).

**Step 4.2 - Link Issues:**

Build hierarchy from bottom-up:

```bash
# First: Link tasks to groups
scripts/link-sub-issues.sh "GROUP1_NODE_ID" "TASK1_ID TASK2_ID TASK3_ID"

# Then: Link groups to epic
scripts/link-sub-issues.sh "EPIC_NODE_ID" "GROUP1_ID GROUP2_ID GROUP3_ID"
```

For manual GraphQL patterns or batch mutations, see `references/graphql-api.md` (grep: `addSubIssue`, `2-Level Hierarchy`).

**Step 4.3 - Verify:**

Check the hierarchy structure:

```bash
scripts/verify-hierarchy.sh OWNER REPO EPIC_NUMBER 2
```

### Phase 5: Iteration

Test the hierarchy in practice and adjust as needed.

**Reorganization:**
Move sub-issues between parents if grouping needs adjustment. See `references/graphql-api.md` (grep: `Reorganizing Existing`) for the remove-then-add pattern.

**Flexibility:**
Hierarchies are not permanent. Split oversized groups, merge sparse groups, or reorganize based on team feedback.

## Helper Scripts

All scripts are in `scripts/` directory and executable:

**`get-node-ids.sh`** - Batch query for GraphQL node IDs
```bash
scripts/get-node-ids.sh OWNER REPO "106 107 108"
```
Use before mutations to gather all required node IDs efficiently.

**`link-sub-issues.sh`** - Link multiple issues to a parent
```bash
scripts/link-sub-issues.sh PARENT_NODE_ID "CHILD1_ID CHILD2_ID CHILD3_ID"
```
Use when building hierarchies to batch-link sub-issues.

**`verify-hierarchy.sh`** - Display issue hierarchy with formatting
```bash
scripts/verify-hierarchy.sh OWNER REPO ISSUE_NUMBER [MAX_DEPTH]
```
Use after building hierarchies to verify structure.

## Reference Files

Detailed information is organized in `references/` for on-demand loading:

**`references/graphql-api.md`** (~150 lines)
- Complete GraphQL patterns and examples
- Query formats for node IDs
- Mutation patterns for add/remove operations
- Batch operation techniques
- API limitations and resources

**`references/best-practices.md`** (~200 lines)
- Organizational principles and hierarchy design
- Parent issue content guidelines and writing style
- Common organizational patterns (scattered features, test coverage, migrations)
- Quality checklist and workflow efficiency tips

**`references/case-study.md`** (~95 lines)
- Real-world example: organizing 26 REST API issues
- Complete implementation walkthrough
- Key decisions and lessons learned
- Demonstrates 2-level hierarchy (Epic → Groups → Tasks)

**When to Load References:**
- Load `graphql-api.md` when performing GraphQL operations or debugging API issues
- Load `best-practices.md` when designing hierarchies or writing parent issue content
- Load `case-study.md` when explaining the approach or showing real-world examples

Use grep patterns documented in each file for quick navigation to specific sections.

## Templates

**`templates/parent-issue-template.md`**
Ready-to-use template for creating parent/epic issues with all recommended sections pre-structured. Customize for each specific epic.

## Key Success Factors

1. **Comprehensive analysis** - Understand all issues before designing structure
2. **Thematic grouping** - Group by natural concerns, not arbitrarily
3. **Quality parent issues** - Provide architectural guidance, not just task lists
4. **Batch operations** - Use scripts and batch queries for efficiency
5. **Bottom-up linking** - Link tasks→groups first, then groups→epic
6. **Verification** - Always verify hierarchy after building

## Technical Notes

- GitHub sub-issues feature released January 2025
- GraphQL API required (no `gh issue` commands for sub-issues yet)
- Must use node IDs in mutations (issue numbers don't work)
- Max 100 sub-issues per parent, max 8 levels of nesting
- Cross-repository sub-issues supported (within same org)

For detailed API information, see `references/graphql-api.md`.
