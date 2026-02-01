# Example: REST API Modernization Epic

This is a real-world example from organizing 26 scattered REST API issues into a cohesive 2-level hierarchy.

## Problem

- 26 issues about REST API improvements scattered across the backlog
- No clear organization or priority
- Difficult to track progress on API modernization
- Issues ranged from error handling to caching to pagination

## Solution Structure

**Epic Level:**
- Issue #106: "REST API Modernization: HTTP/REST Standards Compliance"

**Group Level (7 groups):**
- Issue #107: Error Handling & HTTP Status Codes (7 sub-issues)
- Issue #108: Concurrency Control - ETags (2 sub-issues)
- Issue #109: Idempotency (2 sub-issues)
- Issue #110: HTTP Caching (5 sub-issues)
- Issue #111: Content Negotiation (2 sub-issues)
- Issue #112: RESTful URI Design (6 sub-issues)
- Issue #113: Pagination (2 sub-issues)

**Task Level:**
- Individual implementation issues (e.g., "Implement RFC 9457 Problem Details")

## Key Decisions

1. **Grouped by Technical Concern**: Each group represents a distinct REST/HTTP concern (errors, caching, etc.)
2. **2-Level Hierarchy**: Epic → Groups → Tasks (avoided going deeper)
3. **Comprehensive Parent Issue**: Epic included architectural principles, RFCs, design decisions
4. **Group Issues as Context**: Each group provided specific guidance for that concern

## Epic Issue Content Highlights

```markdown
# REST API Modernization: HTTP/REST Standards Compliance

## Context
Our REST API has grown organically without consistent adherence to HTTP/REST standards.
This creates confusion for API consumers and makes the API harder to maintain.

## Architectural Principles

### 1. Error Responses (RFC 9457)
Use Problem Details format for all error responses...

### 2. Optimistic Concurrency (ETags)
Implement ETags using revision numbers...

[etc.]
```

## Implementation Approach

### Phase 1: Get Node IDs (26 task issues + 7 group issues + 1 epic)
```bash
./scripts/get-node-ids.sh dreamplug-tech weave "48 49 50 ... 107 108 ... 106"
```

### Phase 2: Link Tasks to Groups
```bash
# Group #107 gets tasks #48, #49, #55, #56, #62, #66, #68
./scripts/link-sub-issues.sh "I_kwDOPdtIAs7SF9uh" \
  "I_kwDOPdtIAs7Nl4hs I_kwDOPdtIAs7Nl4i7 I_kwDOPdtIAs7Nl4jp ..."
```

### Phase 3: Link Groups to Epic
```bash
# Epic #106 gets groups #107-#113
./scripts/link-sub-issues.sh "I_kwDOPdtIAs7SF8sD" \
  "I_kwDOPdtIAs7SF9uh I_kwDOPdtIAs7SF9ul I_kwDOPdtIAs7SF9up ..."
```

### Phase 4: Verify
```bash
./scripts/verify-hierarchy.sh dreamplug-tech weave 106 2
```

## Results

- **Before**: 26 scattered issues in backlog
- **After**: 1 trackable epic with clear structure
- **Developer Experience**: Clear roadmap, architectural guidance, incremental implementation path
- **Project Management**: Single epic to track entire API modernization initiative

## Lessons Learned

1. **Group Size**: 2-7 items per group worked well (not too granular, not too broad)
2. **Thematic Grouping**: Grouping by technical concern (errors, caching) > arbitrary grouping
3. **Epic Content**: Comprehensive architectural guidance in epic was crucial
4. **Flexibility**: Can reorganize later if grouping doesn't work in practice
