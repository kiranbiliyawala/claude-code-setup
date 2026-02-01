---
name: databricks-sql
description: Execute SQL queries on Databricks warehouses. This skill should be used when the user asks to query Databricks, run SQL against a Databricks warehouse, check table schemas, or analyze data stored in Databricks. Trigger phrases include "query databricks", "run sql on databricks", "check this table", or references to Databricks catalogs/schemas.
---

# Databricks SQL

## Overview

This skill provides an agent-native CLI for executing SQL queries on Databricks SQL warehouses. The CLI outputs structured JSON, requires no installation (runs via uv), and handles long-running analytics queries gracefully.

## Quick Start

### Prerequisites

1. **uv** must be installed (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
2. Databricks credentials via environment variables or `.env` file

### Configuration

Set these environment variables (or create a `.env` file):

```bash
DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
DATABRICKS_TOKEN=dapi...
DATABRICKS_WAREHOUSE_ID=abc123def456
```

### Running Queries

```bash
# Run the CLI directly (uv auto-installs dependencies)
uv run /path/to/scripts/databricks-sql-cli.py query --sql "SELECT * FROM catalog.schema.table LIMIT 10"
```

## Commands

### query - Execute SQL

```bash
uv run databricks-sql-cli.py query --sql "SELECT 1 as id"
```

**Execution Modes:**

- **Default (hybrid)**: Waits 10s, returns query_id if still running
- **`--async`**: Returns immediately with query_id
- **`--wait`**: Waits indefinitely until completion

**Output Formats:**

- **`--format=json`** (default): JSON to stdout
- **`--format=csv --output-dir=/path`**: Writes CSV file, returns path in JSON

**Example Response:**

```json
{
  "query_id": "01f0e566-...",
  "status": "SUCCEEDED",
  "columns": [{ "name": "id", "type": "INT" }],
  "row_count": 1,
  "data": [{ "id": "1" }]
}
```

### query-status - Check Query Status

```bash
uv run databricks-sql-cli.py query-status --query-id=01f0e566-...
```

### query-cancel - Cancel Running Query

```bash
uv run databricks-sql-cli.py query-cancel --query-id=01f0e566-...
```

### warehouses - List Warehouses

```bash
uv run databricks-sql-cli.py warehouses
```

### config-test - Test Connection

```bash
uv run databricks-sql-cli.py config-test
```

### --schema-info - Get CLI Schema

```bash
uv run databricks-sql-cli.py --schema-info
```

## Handling Long-Running Queries

Analytics queries often take minutes. The CLI handles this with hybrid mode:

1. **Initial wait (10s)**: Query starts, CLI waits 10 seconds
2. **If completed**: Returns results directly
3. **If still running**: Returns query_id with poll/cancel commands

```json
{
  "query_id": "01f0e566-...",
  "status": "RUNNING",
  "mode": "async_fallback",
  "message": "Query still running after 10s",
  "poll_command": "databricks-sql-cli query-status --query-id=01f0e566-...",
  "cancel_command": "databricks-sql-cli query-cancel --query-id=01f0e566-..."
}
```

To poll until completion, use `--wait`:

```bash
uv run databricks-sql-cli.py query --sql "SELECT ..." --wait
```

## Exit Codes

| Code | Meaning              |
| ---- | -------------------- |
| 0    | Success              |
| 1    | General error        |
| 2    | Invalid arguments    |
| 3    | Authentication error |
| 4    | Authorization error  |
| 5    | Resource not found   |
| 7    | Rate limited         |
| 9    | Query cancelled      |

## Common Patterns

### Describe a Table

```bash
uv run databricks-sql-cli.py query --sql "DESCRIBE TABLE catalog.schema.table"
```

### Count Rows

```bash
uv run databricks-sql-cli.py query --sql "SELECT COUNT(*) as cnt FROM catalog.schema.table"
```

### Export to CSV

```bash
uv run databricks-sql-cli.py query \
  --sql "SELECT * FROM catalog.schema.table LIMIT 1000" \
  --format=csv \
  --output-dir=/tmp
```

### Pass SQL from File

```bash
uv run databricks-sql-cli.py query --sql-file=/path/to/query.sql --wait
```

## Resources

### scripts/

- **databricks-sql-cli.py** - The standalone CLI script (PEP 723, runs with uv)

### references/

- **error-codes.md** - Complete error code reference with troubleshooting
