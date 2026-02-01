# Error Codes Reference

## Error Response Format

All errors are returned as structured JSON:

```json
{
  "error": "ERROR_TYPE",
  "code": "E####",
  "message": "Human-readable description",
  "suggestion": "How to fix",
  "field": "affected_field",
  "documentation": "https://docs.databricks.com/..."
}
```

## Configuration Errors (E20xx)

| Code  | Error Type       | Message                                            | Solution                                                        |
| ----- | ---------------- | -------------------------------------------------- | --------------------------------------------------------------- |
| E2001 | CONFIG_MISSING   | Required configuration 'host' not provided         | Set DATABRICKS_HOST env var or use --host flag                  |
| E2002 | CONFIG_MISSING   | Required configuration 'token' not provided        | Set DATABRICKS_TOKEN env var, use --token flag, or --token-file |
| E2003 | CONFIG_MISSING   | Required configuration 'warehouse_id' not provided | Set DATABRICKS_WAREHOUSE_ID env var or use --warehouse flag     |
| E2004 | INVALID_ARGUMENT | Invalid JSON in --context                          | Ensure --context contains valid JSON                            |
| E2005 | CONFIG_ERROR     | Token file not found                               | Check the path to your token file                               |
| E2006 | CONFIG_ERROR     | Permission denied reading token file               | Check file permissions (should be readable)                     |
| E2007 | INVALID_ARGUMENT | No SQL statement provided                          | Use --sql, --sql-file, or --sql-stdin                           |
| E2008 | INVALID_ARGUMENT | Invalid JSON in --params                           | Ensure --params contains valid JSON object                      |
| E2009 | INVALID_ARGUMENT | --output-dir is required when using --format=csv   | Specify --output-dir=/path/to/directory                         |
| E2010 | INVALID_ARGUMENT | Output directory does not exist                    | Create the directory or specify an existing one                 |
| E2011 | INVALID_ARGUMENT | Output path is not a directory                     | Specify a directory path, not a file path                       |

## Authentication Errors (E30xx)

| Code  | Error Type       | Message                                          | Solution                                   |
| ----- | ---------------- | ------------------------------------------------ | ------------------------------------------ |
| E3001 | AUTH_ERROR       | Authentication failed - invalid or expired token | Verify your token is valid and not expired |
| E3002 | CONNECTION_ERROR | Connection test failed                           | Verify host URL and token are correct      |

## Authorization Errors (E40xx)

| Code  | Error Type          | Message                                  | Solution                                           |
| ----- | ------------------- | ---------------------------------------- | -------------------------------------------------- |
| E4001 | AUTHORIZATION_ERROR | Access denied - insufficient permissions | Check your permissions for this warehouse/resource |

## Not Found Errors (E50xx)

| Code  | Error Type     | Message                                      | Solution                                |
| ----- | -------------- | -------------------------------------------- | --------------------------------------- |
| E5001 | FILE_NOT_FOUND | SQL file not found                           | Check the path to your SQL file         |
| E5002 | NOT_FOUND      | Resource not found (warehouse may not exist) | Verify warehouse ID is correct          |
| E5003 | NOT_FOUND      | Query not found                              | Query may have expired or ID is invalid |

## Rate Limiting (E70xx)

| Code  | Error Type   | Message                          | Solution                                |
| ----- | ------------ | -------------------------------- | --------------------------------------- |
| E7001 | RATE_LIMITED | Too many requests - rate limited | Wait and retry with exponential backoff |

## Query Errors (E90xx)

| Code  | Error Type      | Message             | Solution                   |
| ----- | --------------- | ------------------- | -------------------------- |
| E9001 | QUERY_CANCELLED | Query was cancelled | Re-run the query if needed |
| E9002 | QUERY_CLOSED    | Query was closed    | Re-run the query           |

## Execution Errors (E10xx)

| Code  | Error Type      | Message                       | Solution                            |
| ----- | --------------- | ----------------------------- | ----------------------------------- |
| E1000 | EXECUTION_ERROR | Various                       | Check the error message for details |
| E1001 | SQL_ERROR       | SQL syntax or execution error | Fix the SQL query                   |
| E1002 | STATUS_ERROR    | Failed to get query status    | Check query ID is valid             |
| E1003 | CANCEL_ERROR    | Failed to cancel query        | Query may have already completed    |
| E1004 | LIST_ERROR      | Failed to list warehouses     | Check permissions                   |

## Troubleshooting

### "Authentication failed"

1. Check your token hasn't expired
2. Verify DATABRICKS_HOST includes `https://`
3. Ensure token starts with `dapi`

### "Warehouse not found"

1. Run `databricks-sql-cli warehouses` to list available warehouses
2. Copy the correct warehouse ID
3. Ensure the warehouse is not stopped/deleted

### "Rate limited"

1. Wait 30-60 seconds before retrying
2. Reduce query frequency
3. Consider using async mode for bulk operations

### "Query still running after 10s"

This is not an error - it's the hybrid mode returning early. Options:

1. Poll with `query-status --query-id=...`
2. Cancel with `query-cancel --query-id=...`
3. Use `--wait` to wait indefinitely
