# GitHub GraphQL API Patterns for Sub-Issues

This reference contains detailed GraphQL patterns for working with GitHub sub-issues.

## Core Concepts

### GitHub Sub-Issues Feature
- Released publicly in January 2025
- Supports up to 8 levels of nesting
- Up to 100 sub-issues per parent
- Existing issues can be converted to sub-issues
- Cross-repository sub-issues supported (within same org)

### Why GraphQL is Required
The GitHub CLI (`gh`) doesn't have dedicated sub-issue commands yet. All sub-issue operations require GraphQL API through `gh api graphql`.

## Essential Operations

### Query for Node IDs

Issue numbers cannot be used directly in mutations. Always query for GraphQL node IDs first.

**Single Issue:**
```bash
gh api graphql -f query='
  query {
    repository(owner: "OWNER", name: "REPO") {
      issue(number: 123) {
        id
        number
        title
      }
    }
  }
'
```

**Batch Query (Multiple Issues):**
```bash
gh api graphql -f query='
  query {
    repository(owner: "OWNER", name: "REPO") {
      parent: issue(number: 106) { id number title }
      group1: issue(number: 107) { id number title }
      task1: issue(number: 48) { id number title }
      task2: issue(number: 55) { id number title }
    }
  }
'
```

Use aliases (parent:, group1:, task1:) to make results clear when querying multiple issues.

### Add Sub-Issue

Link an existing issue as a sub-issue of a parent:

```bash
gh api graphql -f query='
  mutation {
    addSubIssue(input: {
      issueId: "I_kwDOPdtIAs7SF8sD"
      subIssueId: "I_kwDOPdtIAs7Nl4hs"
    }) {
      issue {
        title
        number
      }
    }
  }
'
```

**Batch Add (Multiple Sub-Issues):**
```bash
gh api graphql -f query='
  mutation {
    g1t1: addSubIssue(input: {
      issueId: "GROUP1_ID"
      subIssueId: "TASK1_ID"
    }) { issue { title } }

    g1t2: addSubIssue(input: {
      issueId: "GROUP1_ID"
      subIssueId: "TASK2_ID"
    }) { issue { title } }

    g1t3: addSubIssue(input: {
      issueId: "GROUP1_ID"
      subIssueId: "TASK3_ID"
    }) { issue { title } }
  }
'
```

Use mutation aliases (g1t1:, g1t2:) for clarity in batch operations.

### Remove Sub-Issue

Unlink a sub-issue from its parent:

```bash
gh api graphql -f query='
  mutation {
    removeSubIssue(input: {
      issueId: "PARENT_ID"
      subIssueId: "CHILD_ID"
    }) {
      issue {
        title
        number
      }
    }
  }
'
```

### Verify Hierarchy

Query the complete sub-issue tree:

```bash
gh api graphql -f query='
  query {
    repository(owner: "OWNER", name: "REPO") {
      issue(number: 106) {
        title
        number
        state
        subIssues(first: 100) {
          nodes {
            number
            title
            state
            subIssues(first: 100) {
              nodes {
                number
                title
                state
              }
            }
          }
        }
      }
    }
  }
'
```

## Common Patterns

### Building 2-Level Hierarchy (Epic → Groups → Tasks)

Follow this order to build clean hierarchies:

1. **Link tasks to groups first:**
```bash
gh api graphql -f query='
  mutation {
    # Group 1 gets its tasks
    g1t1: addSubIssue(input: {issueId: "GROUP1_ID", subIssueId: "TASK1_ID"}) { issue { title } }
    g1t2: addSubIssue(input: {issueId: "GROUP1_ID", subIssueId: "TASK2_ID"}) { issue { title } }

    # Group 2 gets its tasks
    g2t1: addSubIssue(input: {issueId: "GROUP2_ID", subIssueId: "TASK3_ID"}) { issue { title } }
    g2t2: addSubIssue(input: {issueId: "GROUP2_ID", subIssueId: "TASK4_ID"}) { issue { title } }
  }
'
```

2. **Then link groups to epic:**
```bash
gh api graphql -f query='
  mutation {
    epicG1: addSubIssue(input: {issueId: "EPIC_ID", subIssueId: "GROUP1_ID"}) { issue { title } }
    epicG2: addSubIssue(input: {issueId: "EPIC_ID", subIssueId: "GROUP2_ID"}) { issue { title } }
  }
'
```

### Reorganizing Existing Hierarchies

To move a sub-issue from one parent to another:

```bash
gh api graphql -f query='
  mutation {
    # Step 1: Remove from old parent
    remove: removeSubIssue(input: {
      issueId: "OLD_PARENT_ID"
      subIssueId: "CHILD_ID"
    }) { issue { title } }

    # Step 2: Add to new parent
    add: addSubIssue(input: {
      issueId: "NEW_PARENT_ID"
      subIssueId: "CHILD_ID"
    }) { issue { title } }
  }
'
```

Both operations can be combined in a single mutation for atomicity.

## Performance Optimization

### Batch Operations
- Query all node IDs upfront before performing mutations
- Use mutation aliases to execute multiple operations in one call
- Reduces API calls and improves efficiency

### Testing Strategy
- Test hierarchy building with a small subset of issues first
- Verify structure before applying to full issue list
- Use `verify-hierarchy.sh` script to check results

## API Limitations

- GraphQL API only (no `gh issue` commands for sub-issues)
- Must query for node IDs (issue numbers don't work in mutations)
- Max 100 sub-issues per parent
- Max 8 levels of nesting
- Feature is new (Jan 2025), documentation still evolving

## Resources

- [GitHub Sub-Issues Announcement](https://github.blog/changelog/2025-01-15-sub-issues-public-beta/)
- [GraphQL API Reference](https://docs.github.com/en/graphql)
- GitHub Web UI: "Add existing issue" dropdown for manual linking

## Grep Patterns for Quick Reference

Search this file for specific operations:
- `addSubIssue` - Adding sub-issues
- `removeSubIssue` - Removing sub-issues
- `Batch` - Batch operation examples
- `2-Level Hierarchy` - Epic → Groups → Tasks pattern
- `Verify Hierarchy` - Query patterns for checking structure
