# Agent CLI Design Patterns Reference

This reference provides detailed examples, anti-patterns, and implementation guidance for each design principle.

## Pattern 1: Structured Output

### Schema Definition

Define output schemas using JSON Schema and make them discoverable:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "StatusResponse",
  "type": "object",
  "required": ["status", "uptime_seconds", "memory"],
  "properties": {
    "status": {
      "type": "string",
      "enum": ["running", "stopped", "starting", "error"]
    },
    "uptime_seconds": {
      "type": "integer",
      "minimum": 0
    },
    "memory": {
      "type": "object",
      "properties": {
        "used_bytes": {"type": "integer"},
        "total_bytes": {"type": "integer"},
        "percent": {"type": "number", "minimum": 0, "maximum": 100}
      }
    }
  }
}
```

### Anti-patterns to Avoid

```bash
# ANTI-PATTERN: Mixed formats
$ tool list
ID    NAME      STATUS
1     foo       active
2     bar       inactive
Total: 2 items

# ANTI-PATTERN: Inconsistent key naming
$ tool get 1
{"ID": "1", "name": "foo", "Status": "active"}

# ANTI-PATTERN: Locale-dependent formatting
$ tool stats
Memory: 1,234.56 MB  # Comma as thousands separator varies by locale
```

### Correct Implementation

```bash
# CORRECT: Consistent JSON with documented schema
$ tool list
{"items": [{"id": "1", "name": "foo", "status": "active"}, {"id": "2", "name": "bar", "status": "inactive"}], "total": 2, "page": 1, "per_page": 100}

# CORRECT: Consistent snake_case keys
$ tool get 1
{"id": "1", "name": "foo", "status": "active", "created_at": "2025-01-15T10:30:00Z"}

# CORRECT: Raw numeric values, ISO timestamps
$ tool stats
{"memory_bytes": 1294336000, "memory_human": "1.21 GB", "timestamp": "2025-01-15T10:30:00Z"}
```

## Pattern 2: Error Response Structure

### Standard Error Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "ErrorResponse",
  "type": "object",
  "required": ["error", "code", "message"],
  "properties": {
    "error": {
      "type": "string",
      "description": "Error category for programmatic handling",
      "enum": [
        "VALIDATION_ERROR",
        "AUTH_ERROR",
        "AUTHZ_ERROR",
        "NOT_FOUND",
        "CONFLICT",
        "RATE_LIMIT",
        "INTERNAL_ERROR",
        "NETWORK_ERROR"
      ]
    },
    "code": {
      "type": "string",
      "description": "Specific error code for lookup",
      "pattern": "^E[0-9]{4}$"
    },
    "message": {
      "type": "string",
      "description": "Human-readable error message"
    },
    "field": {
      "type": "string",
      "description": "Field that caused validation error"
    },
    "suggestion": {
      "type": "string",
      "description": "Actionable fix suggestion"
    },
    "valid_values": {
      "type": "array",
      "items": {"type": "string"},
      "description": "Valid options if applicable"
    },
    "documentation": {
      "type": "string",
      "format": "uri",
      "description": "Link to relevant documentation"
    },
    "retry_after_seconds": {
      "type": "integer",
      "description": "For rate limiting, when to retry"
    }
  }
}
```

### Error Code Registry

| Code  | Error Type       | Meaning                          |
|-------|------------------|----------------------------------|
| E1001 | VALIDATION_ERROR | Missing required field           |
| E1002 | VALIDATION_ERROR | Invalid field value              |
| E1003 | VALIDATION_ERROR | Field value out of range         |
| E2001 | AUTH_ERROR       | Invalid credentials              |
| E2002 | AUTH_ERROR       | Expired credentials              |
| E2003 | AUTHZ_ERROR      | Insufficient permissions         |
| E3001 | NOT_FOUND        | Resource does not exist          |
| E3002 | NOT_FOUND        | Parent resource does not exist   |
| E4001 | CONFLICT         | Resource already exists          |
| E4002 | CONFLICT         | Concurrent modification detected |
| E5001 | RATE_LIMIT       | Too many requests                |
| E9001 | INTERNAL_ERROR   | Unexpected server error          |

### Error Examples

```bash
# Validation error with suggestions
$ tool create --name ""
{
  "error": "VALIDATION_ERROR",
  "code": "E1002",
  "field": "name",
  "message": "Name cannot be empty",
  "suggestion": "Provide a non-empty name with 1-64 characters"
}

# Rate limit with retry timing
$ tool sync --all
{
  "error": "RATE_LIMIT",
  "code": "E5001",
  "message": "Rate limit exceeded",
  "retry_after_seconds": 60,
  "suggestion": "Wait 60 seconds or use --rate-limit flag to reduce request rate"
}

# Not found with context
$ tool get project-abc
{
  "error": "NOT_FOUND",
  "code": "E3001",
  "message": "Project 'project-abc' not found",
  "suggestion": "Use 'tool list projects' to see available projects",
  "similar": ["project-ab", "project-abcd"]
}
```

## Pattern 3: Batch Operations

### Input Formats

Support multiple input methods for batch operations:

```bash
# JSON array flag
$ tool delete --items='["id1", "id2", "id3"]'

# Newline-delimited stdin
$ echo -e "id1\nid2\nid3" | tool delete --stdin

# JSON Lines stdin
$ cat items.jsonl | tool process --stdin-format=jsonl

# File reference
$ tool delete --items-file=items.json
```

### Batch Response Structure

```json
{
  "results": [
    {"id": "id1", "status": "success", "result": {"deleted": true}},
    {"id": "id2", "status": "success", "result": {"deleted": true}},
    {"id": "id3", "status": "error", "error": {"error": "NOT_FOUND", "code": "E3001"}}
  ],
  "summary": {
    "total": 3,
    "succeeded": 2,
    "failed": 1,
    "duration_ms": 150
  }
}
```

### Batch Behavior Flags

```bash
# Stop on first error (default: continue)
$ tool process --items='[...]' --fail-fast

# Limit concurrency
$ tool process --items='[...]' --concurrency=5

# Return only failures
$ tool process --items='[...]' --output=failures

# Dry run for batch
$ tool process --items='[...]' --dry-run
```

## Pattern 4: Pagination

### Cursor-Based Pagination (Preferred)

```bash
# First request
$ tool list
{
  "items": [...],
  "cursor": "eyJpZCI6MTAwfQ==",
  "has_more": true
}

# Next page
$ tool list --cursor="eyJpZCI6MTAwfQ=="
{
  "items": [...],
  "cursor": "eyJpZCI6MjAwfQ==",
  "has_more": true
}
```

### Offset Pagination

```bash
$ tool list --page=2 --per-page=50
{
  "items": [...],
  "pagination": {
    "page": 2,
    "per_page": 50,
    "total_items": 234,
    "total_pages": 5
  }
}
```

### Fetch All Pattern

```bash
# Single command to fetch all with internal pagination
$ tool list --all
{
  "items": [...],  # All 234 items
  "fetched_pages": 5,
  "total_items": 234
}
```

## Pattern 5: Dry Run and Validation

### Validation Response

```bash
$ tool deploy --config=app.yaml --validate-only
{
  "valid": true,
  "config": {
    "resolved": {
      "name": "my-app",
      "replicas": 3,
      "memory": "512Mi"
    },
    "defaults_applied": {
      "replicas": "3 (default)",
      "memory": "512Mi (default)"
    },
    "warnings": [
      {"field": "image", "message": "Using latest tag is not recommended"}
    ]
  }
}
```

### Dry Run Response

```bash
$ tool deploy --config=app.yaml --dry-run
{
  "would_execute": [
    {"action": "create", "resource": "deployment/my-app", "namespace": "default"},
    {"action": "create", "resource": "service/my-app", "namespace": "default"},
    {"action": "update", "resource": "configmap/my-app", "namespace": "default", "diff": "..."}
  ],
  "summary": {
    "create": 2,
    "update": 1,
    "delete": 0
  }
}
```

## Pattern 6: Long-Running Operations

### Async Pattern with Polling

```bash
# Start operation, get operation ID
$ tool migrate --async
{
  "operation_id": "op_abc123",
  "status": "pending",
  "poll_url": "tool status op_abc123",
  "estimated_duration_seconds": 300
}

# Poll for status
$ tool status op_abc123
{
  "operation_id": "op_abc123",
  "status": "running",
  "progress": {"completed": 50, "total": 100},
  "started_at": "2025-01-15T10:30:00Z"
}

# Final result
$ tool status op_abc123
{
  "operation_id": "op_abc123",
  "status": "completed",
  "result": {...},
  "started_at": "2025-01-15T10:30:00Z",
  "completed_at": "2025-01-15T10:35:00Z"
}
```

### Streaming Events (NDJSON)

```bash
$ tool migrate --stream
{"event": "started", "operation_id": "op_abc123", "total": 100}
{"event": "progress", "completed": 10, "current": "table_users"}
{"event": "progress", "completed": 20, "current": "table_orders"}
{"event": "warning", "message": "Skipped 3 invalid rows", "table": "table_orders"}
{"event": "progress", "completed": 100, "current": "table_audit"}
{"event": "completed", "duration_ms": 300000, "migrated": 100, "warnings": 1}
```

## Pattern 7: Authentication

### Token Passing

```bash
# Environment variable (documented default)
$ export TOOL_TOKEN="xxx"
$ tool list

# Explicit flag (always overrides)
$ tool list --token="xxx"

# Token file reference
$ tool list --token-file=/path/to/token

# Stdin for sensitive operations
$ echo "xxx" | tool list --token-stdin
```

### Auth Status Introspection

```bash
$ tool auth status
{
  "authenticated": true,
  "method": "api_token",
  "identity": "user@example.com",
  "permissions": ["read", "write"],
  "expires_at": "2025-02-15T10:30:00Z"
}
```

## Pattern 8: Context and Configuration

### Configuration Precedence

Document clear precedence (later overrides earlier):

1. Built-in defaults
2. System config file (`/etc/tool/config.yaml`)
3. User config file (`~/.tool/config.yaml`)
4. Project config file (`./tool.yaml`)
5. Environment variables (`TOOL_*`)
6. Command-line flags

### Config Introspection

```bash
$ tool config show
{
  "effective": {
    "region": "us-west-2",
    "timeout": 30
  },
  "sources": {
    "region": {"value": "us-west-2", "source": "env:TOOL_REGION"},
    "timeout": {"value": 30, "source": "default"}
  }
}

$ tool config validate
{
  "valid": true,
  "warnings": [
    {"key": "legacy_option", "message": "Deprecated, use new_option instead"}
  ]
}
```

## Pattern 9: Versioning and Compatibility

### Version Information

```bash
$ tool --version
{
  "version": "2.3.1",
  "api_version": "v2",
  "build": "abc123",
  "go_version": "1.21",
  "platform": "darwin/arm64",
  "features": ["batch", "transactions", "streaming"]
}
```

### API Version Selection

```bash
# Explicit API version
$ tool list --api-version=v1

# Check version compatibility
$ tool --check-compatibility
{
  "client_version": "2.3.1",
  "server_version": "2.4.0",
  "compatible": true,
  "deprecation_warnings": [
    {"feature": "v1-api", "deprecated_at": "2025-01-01", "removal_at": "2026-01-01"}
  ]
}
```

## Anti-Pattern Summary

| Anti-Pattern | Problem | Solution |
|-------------|---------|----------|
| Pretty tables by default | Not parseable | JSON default, `--format=table` option |
| Interactive prompts | Blocks automation | Flags for all input |
| Implicit cwd | Non-reproducible | Explicit `--path` or `--project` |
| Exit code 1 for all errors | No error classification | Specific exit codes per error type |
| Progress bars | Not parseable | NDJSON events with progress |
| `--quiet` changes structure | Unpredictable output | Consistent structure always |
| Locale-dependent numbers | Parsing breaks | Raw numbers, ISO formats |
| TTY detection | Different behavior | Consistent regardless of TTY |
| Pagination without cursors | Race conditions | Cursor-based pagination |
| Secrets in command line | Visible in ps | Env vars or file references |
