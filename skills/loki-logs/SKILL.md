---
name: loki-logs
description: Query logs from Loki (stage/prod environments). This skill should be used when the user asks to fetch logs, search for errors, debug issues by correlation ID, list services, or investigate application behavior from log data. Trigger phrases include "check logs", "find errors in", "what happened for correlation id", "debug this issue", "list services", or any log investigation request.
---

# Loki Logs

## Overview

Query logs from internal Loki instances (stage/prod) using logcli (official Grafana CLI). Supports querying by service, correlation ID, preset filters (errors, warnings, exceptions, slow requests, HTTP status codes), and raw LogQL queries.

## Requirements

- `logcli` CLI tool (install via `brew install logcli`)
- Internal network access (VPN/VPC)
- Python 3.10+ (for wrapper script)

## Quick Start

```bash
# Query errors from a service
python scripts/loki_cli.py query --service weave --env stage --preset errors

# Search by correlation ID
python scripts/loki_cli.py query --service weave --env stage --filter "correlation-id-here"

# List available services
python scripts/loki_cli.py services --env stage

# Get query statistics
python scripts/loki_cli.py stats --service weave --env stage --since 1h

# Get log volume
python scripts/loki_cli.py volume --service weave --env stage --since 24h

# List log streams
python scripts/loki_cli.py series --service weave --env stage
```

## Commands

### Query Logs

```bash
python scripts/loki_cli.py query --service <name> --env <stage|prod> [options]
```

| Flag               | Description                                  |
| ------------------ | -------------------------------------------- |
| `--service`        | Service name (subsystemName label)           |
| `--logql`          | Raw LogQL query (alternative to --service)   |
| `--query-file`     | Path to file containing LogQL query (avoids shell escaping) |
| `--env`            | Environment: `stage` or `prod`               |
| `--since`          | Time range: `5m`, `1h`, `24h` (default: 10m) |
| `--limit`          | Max entries (default: 100)                   |
| `--filter`         | Text filter (adds `\|= "text"`)              |
| `--preset`         | Preset filter (see below)                    |
| `--exclude-health` | Exclude health check logs                    |
| `--parallel`       | Use parallel queries for large time ranges   |
| `--format`         | Output: `json` (default) or `human`          |

### Preset Filters

| Preset       | Description                      |
| ------------ | -------------------------------- |
| `errors`     | Error/fatal level logs           |
| `warnings`   | Warning+ level logs              |
| `exceptions` | Stack traces, panics, exceptions |
| `slow`       | Slow requests (>1s)              |
| `5xx`        | HTTP 5xx server errors           |
| `4xx`        | HTTP 4xx client errors           |

### List Services

```bash
python scripts/loki_cli.py services --env <stage|prod> [--filter <pattern>]
```

### List Labels

```bash
python scripts/loki_cli.py labels --env <stage|prod> [--label <name>]
```

### Query Statistics

```bash
python scripts/loki_cli.py stats --service <name> --env <stage|prod> [--since <duration>]
```

Returns bytes processed, chunks, and entries per stream.

### Log Volume

```bash
python scripts/loki_cli.py volume --service <name> --env <stage|prod> [--since <duration>]
```

Returns bytes/entries per stream over time.

### List Log Streams

```bash
python scripts/loki_cli.py series --service <name> --env <stage|prod> [--since <duration>]
```

Returns all stream label combinations matching the query.

## Pattern Discovery Protocol

For ambiguous queries like "show meaningful logs" or "find interesting events", **always sample first** to understand the service's logging patterns before writing filters:

### Step 1: Sample logs to understand patterns

```bash
python scripts/loki_cli.py query --service <name> --env <env> --limit 200 --since 30m --exclude-health --format json
```

### Step 2: Analyze the sample

Parse the JSON output to identify:
- **Event distribution**: Which `event` values dominate? (e.g., `operation_started`, `Request completed`)
- **Level distribution**: Ratio of info/warning/error logs
- **Periodic patterns**: Scheduled tasks, heartbeats, health checks
- **Field names**: What JSON fields exist? (`event`, `operation_name`, `level`, etc.)

Example analysis script:
```python
import json
from collections import Counter

# Parse sample output
entries = data['results']['entries']
events = Counter()
for e in entries:
    inner = json.loads(json.loads(e['message'])['log'])
    events[inner.get('event', 'unknown')] += 1

# Identify noise (>10% of logs)
noise_events = [ev for ev, count in events.items() if count > len(entries) * 0.1]
```

### Step 3: Build targeted query

Use discovered patterns to write exclusion filters. For complex queries with special characters, use `--query-file`.

## Query File Usage

For queries with special characters (negation, pipes, regex patterns), write the query to a file to avoid shell escaping issues:

```bash
# Write query to file
cat > /tmp/query.logql << 'EOF'
{subsystemName="weave"} != "/health" != "operation_started" != "operation_completed" !~ "health_check"
EOF

# Execute from file
python scripts/loki_cli.py query --env stage --query-file /tmp/query.logql --limit 100 --since 1h
```

**LogQL line filter syntax:**

```
|=   line contains string
!=   line does NOT contain string
|~   line matches regex
!~   line does NOT match regex
```

Note: Multiple filters chain together to exclude lines matching any pattern.

## Common Workflows

### Debug by Correlation ID

```bash
python scripts/loki_cli.py query --service weave --env stage --filter "cafa4673-7d74-4696-ab71-496d4764fd13" --since 1h
```

### Find Recent Errors

```bash
python scripts/loki_cli.py query --service hermes --env prod --preset errors --exclude-health --since 30m
```

### Custom LogQL Query

```bash
python scripts/loki_cli.py query --env stage --logql '{subsystemName="weave"} |= "exception"' --since 1h
```

### Custom LogQL from File (Recommended for Complex Queries)

```bash
# Write complex query with exclusions to file
cat > /tmp/query.logql << 'EOF'
{subsystemName="weave"} != "/health" != "operation_started" != "operation_completed" !~ "health_check"
EOF

# Execute
python scripts/loki_cli.py query --env stage --query-file /tmp/query.logql --limit 100 --since 1h
```

### Large Time Range Query (Parallel)

```bash
python scripts/loki_cli.py query --service weave --env stage --since 6h --parallel
```

## Output Format

Default JSON output includes:

- `status`: success/error
- `query`: The LogQL query executed
- `results.entries[]`: Log entries with timestamp, message, labels

Use `--format human` for readable output.

## Resources

### scripts/loki_cli.py

Main CLI tool for querying Loki via logcli. Execute directly without loading into context.

### Reference Documentation

Load these files only when needed for specific use cases:

- **`references/logql-log-queries.md`** (~4k words) - Writing LogQL queries: stream selectors, line filters, parsers (json, logfmt, pattern, regexp), label filters
- **`references/logql-examples.md`** (~800 words) - Practical query examples for common use cases
- **`references/logql-metric-queries.md`** (~1.6k words) - Aggregation functions: rate(), count_over_time(), sum_over_time(), quantile_over_time()
- **`references/logql-best-practices.md`** (~750 words) - Query optimization and efficient patterns
- **`references/logcli-reference.md`** (~11k words) - Full logcli CLI reference. Search with grep for specific flags rather than loading entire file.
