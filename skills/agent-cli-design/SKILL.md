---
name: agent-cli-design
description: Design CLI tool interfaces and behaviors optimized for AI agent consumption. This skill should be used when designing new command-line tools, APIs, or interfaces that will be primarily consumed by AI agents rather than humans. Trigger phrases include "design a CLI for agents", "agent-native interface", "machine-readable CLI", or when discussing how to make tools AI-friendly.
---

# Agent CLI Design

## Overview

This skill guides the design of command-line interfaces optimized for AI agent consumption. Traditional CLIs prioritize human ergonomics: minimal typing, visual formatting, interactive prompts. Agent-native CLIs prioritize machine ergonomics: structured output, explicit state, predictable behavior, and composability.

## Core Design Principles

### 1. Structured Output by Default

Output JSON (or other structured formats) as the default, not via `--json` flag.

**Human-first (avoid):**
```bash
$ tool status
Status: Running
Uptime: 3 days, 2 hours
Memory: 1.2GB / 4GB (30%)
```

**Agent-first (prefer):**
```bash
$ tool status
{"status": "running", "uptime_seconds": 266400, "memory": {"used_bytes": 1288490188, "total_bytes": 4294967296, "percent": 30}}
```

**Design rules:**
- JSON as default output format
- Optional `--format=human` for human-readable output
- Consistent schema across all commands (document with JSON Schema)
- No ANSI colors or formatting codes in default output
- Full data always returned (no truncation without explicit pagination)

### 2. Zero Interactive Prompts

Never require real-time user input. All parameters must be passable via flags or stdin.

**Human-first (avoid):**
```bash
$ tool delete resource-123
Are you sure? (y/n): _
```

**Agent-first (prefer):**
```bash
$ tool delete resource-123 --confirm
{"deleted": "resource-123", "timestamp": "2025-01-15T10:30:00Z"}

$ tool delete resource-123
{"error": "CONFIRMATION_REQUIRED", "message": "Use --confirm flag to delete", "resource": "resource-123"}
```

**Design rules:**
- All confirmations via explicit flags (`--confirm`, `--force`, `--yes`)
- No TTY detection that changes behavior
- Stdin for bulk input, not interactive prompts
- Password/secrets via environment variables or files, not prompts

### 3. Rich Error Taxonomy

Errors should be structured, specific, and actionable.

**Human-first (avoid):**
```bash
$ tool create --name "test"
Error: Invalid configuration
```

**Agent-first (prefer):**
```bash
$ tool create --name "test"
{
  "error": "VALIDATION_ERROR",
  "code": "E1001",
  "field": "region",
  "message": "Region is required when creating resources",
  "suggestion": "Add --region flag with valid region code",
  "valid_values": ["us-east-1", "us-west-2", "eu-west-1"],
  "documentation": "https://docs.tool.com/regions"
}
```

**Design rules:**
- Error codes in addition to messages (machine-parseable)
- Specific error types (VALIDATION_ERROR, AUTH_ERROR, RATE_LIMIT, NOT_FOUND)
- Affected field/resource identification
- Actionable suggestions in structured format
- Partial success reporting for batch operations

### 4. Idempotent Operations

Commands should be safely re-runnable with identical results.

**Design rules:**
- Create operations return existing resource if already exists (with flag to control)
- Update operations accept full desired state, not deltas
- Delete operations succeed silently if resource doesn't exist
- Provide `--if-not-exists`, `--if-exists` modifiers
- Return operation result indicating what actually happened

```bash
$ tool create-bucket my-bucket
{"bucket": "my-bucket", "action": "created", "created_at": "2025-01-15T10:30:00Z"}

$ tool create-bucket my-bucket
{"bucket": "my-bucket", "action": "already_exists", "created_at": "2025-01-14T08:00:00Z"}
```

### 5. Explicit State Passing

No implicit state from environment or session. All context passable as parameters.

**Human-first (avoid):**
```bash
$ cd /project
$ tool init
$ tool build  # implicitly uses /project context
```

**Agent-first (prefer):**
```bash
$ tool build --project=/project --config='{"optimize": true}'
```

**Design rules:**
- Working directory explicitly specified, not assumed from cwd
- Configuration passable as JSON flags, not just files
- No "session" state between commands
- Environment variables documented but always overridable by flags
- Context blob pattern: `--context='{"auth": {...}, "project": {...}}'`

### 6. Batch Operations Native

Support operating on multiple items in single invocation.

**Human-first (avoid):**
```bash
$ tool delete item1
$ tool delete item2
$ tool delete item3
```

**Agent-first (prefer):**
```bash
$ tool delete --items='["item1", "item2", "item3"]'
{
  "results": [
    {"id": "item1", "status": "deleted"},
    {"id": "item2", "status": "deleted"},
    {"id": "item3", "status": "not_found", "error": "RESOURCE_NOT_FOUND"}
  ],
  "summary": {"succeeded": 2, "failed": 1}
}
```

**Design rules:**
- Accept arrays via JSON flags or newline-delimited stdin
- Return results keyed by input identifier, not positional
- Partial failure handling (continue on error, report all results)
- Parallel execution internally when possible

### 7. Transaction Support

Support atomic multi-step operations with rollback capability.

```bash
# Start transaction
$ tool --transaction-start
{"transaction_id": "txn_abc123"}

# Execute operations
$ tool create resource-a --transaction=txn_abc123
$ tool create resource-b --transaction=txn_abc123

# Commit or rollback
$ tool --transaction-commit txn_abc123
{"committed": true, "operations": 2}

# Or rollback
$ tool --transaction-rollback txn_abc123
{"rolled_back": true, "operations_reverted": 2}
```

**Design rules:**
- Transaction IDs for grouping related operations
- Explicit commit/rollback commands
- Automatic rollback on failure (configurable)
- Operation receipts with unique IDs for every mutation

### 8. Capability Introspection

Enable agents to discover what the tool can do programmatically.

```bash
# JSON Schema for all commands
$ tool --schema
{"commands": {"create": {"parameters": {...}}, "delete": {...}}}

# Available capabilities
$ tool --capabilities
{"commands": ["create", "read", "update", "delete"], "features": ["batch", "transactions"]}

# Validate without executing
$ tool create --validate-only --name="test"
{"valid": true, "would_create": {"name": "test", "defaults_applied": {"region": "us-east-1"}}}
```

**Design rules:**
- `--schema` returns JSON Schema for all commands and parameters
- `--capabilities` lists available actions and features
- `--validate-only` checks inputs without side effects
- `--dry-run` shows exactly what would change
- Version/feature detection as structured data

### 9. Streaming with Boundaries

For long-running operations, stream progress as discrete events.

**Human-first (avoid):**
```
Processing... [████████░░░░░░░░] 50%
```

**Agent-first (prefer):**
```bash
$ tool process large-file --stream
{"event": "started", "total_items": 1000}
{"event": "progress", "completed": 100, "total": 1000}
{"event": "progress", "completed": 200, "total": 1000}
...
{"event": "completed", "processed": 1000, "duration_ms": 5000}
```

**Design rules:**
- Newline-delimited JSON (NDJSON) for streaming
- Clear event types (started, progress, completed, error)
- Each line is independently parseable
- Final summary event with complete results

## Command Design Checklist

When designing each command, verify:

- [ ] Default output is structured (JSON)
- [ ] No interactive prompts; all input via flags/stdin
- [ ] Errors include code, message, field, and suggestion
- [ ] Operation is idempotent or clearly documented as not
- [ ] All context passable explicitly (no implicit cwd/session)
- [ ] Batch variant exists for multi-item operations
- [ ] `--dry-run` or `--validate-only` available for mutations
- [ ] Exit codes are meaningful and documented
- [ ] Long operations support `--stream` for progress

## Exit Code Convention

| Code | Meaning | Agent Action |
|------|---------|--------------|
| 0 | Success | Continue |
| 1 | General error | Parse error output |
| 2 | Invalid arguments | Fix arguments |
| 3 | Authentication error | Refresh credentials |
| 4 | Authorization error | Check permissions |
| 5 | Resource not found | Handle missing resource |
| 6 | Conflict | Resolve conflict |
| 7 | Rate limited | Retry with backoff |
| 8 | Partial success | Parse results array |

## Resources

Refer to `references/design-patterns.md` for detailed examples and anti-patterns for each principle.
