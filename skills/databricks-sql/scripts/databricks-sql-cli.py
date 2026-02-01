#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "databricks-sdk>=0.76.0",
#     "python-dotenv>=1.0.0",
# ]
# ///
"""
Databricks SQL CLI - Agent-Native Command Line Interface

A standalone, portable CLI tool optimized for AI agent consumption.
No installation required - just run with uv.

Usage:
    uv run databricks-sql-cli.py query --sql "SELECT 1"
    ./databricks-sql-cli.py query --sql "SELECT 1"  (if chmod +x)
"""

import argparse
import csv
import json
import os
import sys
import time
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from enum import IntEnum
from io import StringIO
from pathlib import Path
from typing import Any, NoReturn

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import (
    Disposition,
    ExecuteStatementRequestOnWaitTimeout,
    Format,
    StatementState,
)
from dotenv import load_dotenv

# Constants
TOKEN_MASK_LENGTH = 8
DEFAULT_HYBRID_TIMEOUT_SECONDS = 10


# Exit codes following agent-cli-design conventions
class ExitCode(IntEnum):
    SUCCESS = 0
    GENERAL_ERROR = 1
    INVALID_ARGUMENTS = 2
    AUTH_ERROR = 3
    AUTHORIZATION_ERROR = 4
    NOT_FOUND = 5
    CONFLICT = 6
    RATE_LIMITED = 7
    PARTIAL_SUCCESS = 8
    CANCELLED = 9
    TIMEOUT = 10


@dataclass
class ErrorResponse:
    error: str
    code: str
    message: str
    suggestion: str | None = None
    field: str | None = None
    documentation: str | None = None
    details: dict | None = None


def output_json(data: Any, exit_code: int = 0) -> NoReturn:
    """Output JSON and exit with specified code."""
    if isinstance(data, ErrorResponse):
        result = {k: v for k, v in asdict(data).items() if v is not None}
    elif hasattr(data, "__dict__"):
        result = data.__dict__
    else:
        result = data
    print(json.dumps(result, indent=2, default=str))
    sys.exit(exit_code)


def output_error(
    error_type: str,
    code: str,
    message: str,
    exit_code: int,
    suggestion: str | None = None,
    field: str | None = None,
    documentation: str | None = None,
    details: dict | None = None,
) -> NoReturn:
    """Output structured error and exit."""
    output_json(
        ErrorResponse(
            error=error_type,
            code=code,
            message=message,
            suggestion=suggestion,
            field=field,
            documentation=documentation,
            details=details,
        ),
        exit_code,
    )


def get_config(args: argparse.Namespace) -> dict:
    """
    Get configuration from flags, env vars, or context blob.
    Priority: flags > context > env vars
    """
    # Load .env file if it exists
    env_path = Path.cwd() / ".env"
    if env_path.exists():
        load_dotenv(env_path)

    # Also check parent directory for .env
    parent_env = Path.cwd().parent / ".env"
    if parent_env.exists():
        load_dotenv(parent_env)

    config = {}

    # If context blob provided, parse it first
    if hasattr(args, "context") and args.context:
        try:
            config = json.loads(args.context)
        except json.JSONDecodeError as e:
            output_error(
                "INVALID_ARGUMENT",
                "E2004",
                f"Invalid JSON in --context: {e}",
                ExitCode.INVALID_ARGUMENTS,
                suggestion="Ensure --context contains valid JSON",
            )

    # Environment variables (lower priority than context)
    env_mapping = {
        "host": "DATABRICKS_HOST",
        "token": "DATABRICKS_TOKEN",
        "warehouse_id": "DATABRICKS_WAREHOUSE_ID",
        "catalog": "DATABRICKS_CATALOG",
        "schema": "DATABRICKS_SCHEMA",
    }

    for key, env_var in env_mapping.items():
        if key not in config and os.environ.get(env_var):
            config[key] = os.environ[env_var]

    # Command-line flags (highest priority)
    flag_mapping = {
        "host": "host",
        "token": "token",
        "warehouse_id": "warehouse",
        "catalog": "catalog",
        "schema": "schema",
    }

    for config_key, flag_name in flag_mapping.items():
        if hasattr(args, flag_name) and getattr(args, flag_name):
            config[config_key] = getattr(args, flag_name)

    # Handle token file
    if hasattr(args, "token_file") and args.token_file:
        try:
            config["token"] = Path(args.token_file).read_text().strip()
        except FileNotFoundError:
            output_error(
                "CONFIG_ERROR",
                "E2005",
                f"Token file not found: {args.token_file}",
                ExitCode.INVALID_ARGUMENTS,
                suggestion="Check the path to your token file",
            )
        except PermissionError:
            output_error(
                "CONFIG_ERROR",
                "E2006",
                f"Permission denied reading token file: {args.token_file}",
                ExitCode.INVALID_ARGUMENTS,
                suggestion="Check file permissions (should be readable)",
            )

    return config


def validate_config(config: dict, required_fields: list[str]) -> None:
    """Validate that required configuration fields are present."""
    missing = [f for f in required_fields if not config.get(f)]

    if missing:
        field = missing[0]
        suggestions = {
            "host": "Set DATABRICKS_HOST env var or use --host flag",
            "token": "Set DATABRICKS_TOKEN env var, use --token flag, or --token-file",
            "warehouse_id": "Set DATABRICKS_WAREHOUSE_ID env var or use --warehouse flag",
        }
        output_error(
            "CONFIG_MISSING",
            f"E200{required_fields.index(field) + 1}",
            f"Required configuration '{field}' not provided",
            ExitCode.INVALID_ARGUMENTS,
            suggestion=suggestions.get(field),
            field=field,
            documentation="https://docs.databricks.com/dev-tools/auth",
        )


def get_client(config: dict) -> WorkspaceClient:
    """Create and return a Databricks WorkspaceClient."""
    try:
        return WorkspaceClient(host=config["host"], token=config["token"])
    except Exception as e:
        output_error(
            "AUTH_ERROR",
            "E3001",
            f"Failed to initialize Databricks client: {e}",
            ExitCode.AUTH_ERROR,
            suggestion="Verify your host URL and token are correct",
            documentation="https://docs.databricks.com/dev-tools/auth",
        )


def cmd_query(args: argparse.Namespace) -> None:
    """Execute a SQL query."""
    config = get_config(args)
    validate_config(config, ["host", "token", "warehouse_id"])

    # Get SQL from args, file, or stdin
    sql = None
    if args.sql:
        sql = args.sql
    elif args.sql_file:
        try:
            sql = Path(args.sql_file).read_text()
        except FileNotFoundError:
            output_error(
                "FILE_NOT_FOUND",
                "E5001",
                f"SQL file not found: {args.sql_file}",
                ExitCode.NOT_FOUND,
                suggestion="Check the path to your SQL file",
            )
    elif args.sql_stdin:
        sql = sys.stdin.read()

    if not sql or not sql.strip():
        output_error(
            "INVALID_ARGUMENT",
            "E2007",
            "No SQL statement provided",
            ExitCode.INVALID_ARGUMENTS,
            suggestion="Use --sql, --sql-file, or --sql-stdin to provide SQL",
        )

    # Validate parameters JSON if provided (for future use with parameterized queries)
    if args.params:
        try:
            json.loads(args.params)  # Validate JSON format
        except json.JSONDecodeError as e:
            output_error(
                "INVALID_ARGUMENT",
                "E2008",
                f"Invalid JSON in --params: {e}",
                ExitCode.INVALID_ARGUMENTS,
                suggestion="Ensure --params contains valid JSON object",
            )

    client = get_client(config)

    # Determine execution mode
    wait_indefinitely = getattr(args, "wait", False)
    async_exec = getattr(args, "async_exec", False)

    try:
        # Databricks API requires wait_timeout between 5-50 seconds, or 0s for async
        # Async mode: 0s (return immediately), otherwise: 10s initial wait
        wait_timeout = "0s" if async_exec else f"{DEFAULT_HYBRID_TIMEOUT_SECONDS}s"

        # Execute statement
        response = client.statement_execution.execute_statement(
            statement=sql,
            warehouse_id=config["warehouse_id"],
            catalog=config.get("catalog"),
            schema=config.get("schema"),
            wait_timeout=wait_timeout,
            on_wait_timeout=ExecuteStatementRequestOnWaitTimeout.CONTINUE,
            row_limit=args.max_rows if hasattr(args, "max_rows") else None,
            format=Format.JSON_ARRAY,
            disposition=Disposition.INLINE,
        )

        statement_id = response.statement_id
        if not statement_id:
            output_error(
                "EXECUTION_ERROR",
                "E1000",
                "No statement ID returned from execute",
                ExitCode.GENERAL_ERROR,
            )

        status = response.status
        status_value = status.state.value if status and status.state else "PENDING"

        # Handle async execution - return immediately
        if async_exec:
            output_json(
                {
                    "query_id": statement_id,
                    "status": status_value,
                    "mode": "async",
                    "submitted_at": datetime.now(UTC).isoformat(),
                }
            )

        # Check if query is still running after initial wait
        is_running = status and status.state in (StatementState.PENDING, StatementState.RUNNING)

        # Hybrid mode: if still running and not --wait, return query_id for polling
        if is_running and not wait_indefinitely:
            output_json(
                {
                    "query_id": statement_id,
                    "status": status_value,
                    "mode": "async_fallback",
                    "message": f"Query still running after {DEFAULT_HYBRID_TIMEOUT_SECONDS}s",
                    "poll_command": f"databricks-sql-cli query-status --query-id={statement_id}",
                    "cancel_command": f"databricks-sql-cli query-cancel --query-id={statement_id}",
                    "submitted_at": datetime.now(UTC).isoformat(),
                }
            )

        # Wait mode or query completed quickly: poll until completion
        while status and status.state in (
            StatementState.PENDING,
            StatementState.RUNNING,
        ):
            time.sleep(1)
            response = client.statement_execution.get_statement(statement_id)
            status = response.status

        # Handle terminal states
        if status and status.state == StatementState.FAILED:
            error_msg = "Unknown error"
            if status.error and status.error.message:
                error_msg = status.error.message
            output_error(
                "SQL_ERROR",
                "E1001",
                error_msg,
                ExitCode.GENERAL_ERROR,
                details={"query_id": statement_id},
            )

        if status and status.state == StatementState.CANCELED:
            output_error(
                "QUERY_CANCELLED",
                "E9001",
                "Query was cancelled",
                ExitCode.CANCELLED,
                details={"query_id": statement_id},
            )

        if status and status.state == StatementState.CLOSED:
            output_error(
                "QUERY_CLOSED",
                "E9002",
                "Query was closed",
                ExitCode.GENERAL_ERROR,
                details={"query_id": statement_id},
            )

        # Build result metadata
        status_str = "UNKNOWN"
        if status and status.state:
            status_str = status.state.value

        # Extract schema info
        columns: list[dict[str, Any]] = []
        col_names: list[str] = []
        if response.manifest:
            schema = response.manifest.schema
            columns = [
                {"name": col.name, "type": col.type_name}
                for col in (schema.columns if schema else []) or []
            ]
            col_names = [c["name"] for c in columns]

        # Extract data
        data_rows: list[list[Any]] = []
        if response.result and response.result.data_array:
            data_rows = response.result.data_array

        # Handle output format
        output_format = getattr(args, "format", "json") or "json"
        output_dir = getattr(args, "output_dir", None)

        if output_format == "csv":
            # CSV format requires output directory
            if not output_dir:
                output_error(
                    "INVALID_ARGUMENT",
                    "E2009",
                    "--output-dir is required when using --format=csv",
                    ExitCode.INVALID_ARGUMENTS,
                    suggestion="Specify --output-dir=/path/to/directory for CSV output",
                )

            # Validate output directory exists
            output_path = Path(output_dir)
            if not output_path.exists():
                output_error(
                    "INVALID_ARGUMENT",
                    "E2010",
                    f"Output directory does not exist: {output_dir}",
                    ExitCode.INVALID_ARGUMENTS,
                    suggestion="Create the directory or specify an existing one",
                )
            if not output_path.is_dir():
                output_error(
                    "INVALID_ARGUMENT",
                    "E2011",
                    f"Output path is not a directory: {output_dir}",
                    ExitCode.INVALID_ARGUMENTS,
                    suggestion="Specify a directory path, not a file path",
                )

            # Generate CSV filename
            timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
            csv_filename = f"query_{statement_id}_{timestamp}.csv"
            csv_path = output_path / csv_filename

            # Write CSV file
            csv_buffer = StringIO()
            writer = csv.writer(csv_buffer)
            writer.writerow(col_names)  # Header
            writer.writerows(data_rows)
            csv_content = csv_buffer.getvalue()

            csv_path.write_text(csv_content)
            file_bytes = csv_path.stat().st_size

            # Return JSON metadata with file info
            result: dict[str, Any] = {
                "query_id": statement_id,
                "status": status_str,
                "format": "csv",
                "file": str(csv_path),
                "row_count": len(data_rows),
                "column_count": len(col_names),
                "bytes": file_bytes,
                "columns": columns,
            }
            if response.manifest:
                result["truncated"] = response.manifest.truncated or False

            output_json(result)

        else:
            # JSON format (default) - output to stdout
            result = {
                "query_id": statement_id,
                "status": status_str,
                "columns": columns,
            }

            if response.manifest:
                result["row_count"] = response.manifest.total_row_count
                result["truncated"] = response.manifest.truncated or False

            # Convert array of arrays to array of objects for JSON
            result["data"] = [dict(zip(col_names, row, strict=False)) for row in data_rows]

            output_json(result)

    except Exception as e:
        error_str = str(e)
        if "401" in error_str or "Unauthorized" in error_str.lower():
            output_error(
                "AUTH_ERROR",
                "E3001",
                "Authentication failed - invalid or expired token",
                ExitCode.AUTH_ERROR,
                suggestion="Verify your token is valid and not expired",
                documentation="https://docs.databricks.com/dev-tools/auth",
            )
        elif "403" in error_str or "Forbidden" in error_str.lower():
            output_error(
                "AUTHORIZATION_ERROR",
                "E4001",
                "Access denied - insufficient permissions",
                ExitCode.AUTHORIZATION_ERROR,
                suggestion="Check your permissions for this warehouse/resource",
            )
        elif "404" in error_str:
            output_error(
                "NOT_FOUND",
                "E5002",
                "Resource not found (warehouse may not exist)",
                ExitCode.NOT_FOUND,
                suggestion="Verify warehouse ID is correct",
                field="warehouse_id",
            )
        elif "429" in error_str or "rate" in error_str.lower():
            output_error(
                "RATE_LIMITED",
                "E7001",
                "Too many requests - rate limited",
                ExitCode.RATE_LIMITED,
                suggestion="Wait and retry with exponential backoff",
            )
        else:
            output_error(
                "EXECUTION_ERROR",
                "E1000",
                str(e),
                ExitCode.GENERAL_ERROR,
            )


def cmd_query_status(args: argparse.Namespace) -> None:
    """Get status of an async query."""
    config = get_config(args)
    validate_config(config, ["host", "token"])

    client = get_client(config)

    try:
        response = client.statement_execution.get_statement(args.query_id)

        status_str = "UNKNOWN"
        if response.status and response.status.state:
            status_str = response.status.state.value
        result: dict[str, Any] = {
            "query_id": args.query_id,
            "status": status_str,
        }

        if response.status and response.status.state == StatementState.RUNNING:
            # Add progress info if available
            pass

        if response.status and response.status.state == StatementState.FAILED:
            result["error"] = response.status.error.message if response.status.error else "Unknown"

        output_json(result)

    except Exception as e:
        if "404" in str(e):
            output_error(
                "NOT_FOUND",
                "E5003",
                f"Query not found: {args.query_id}",
                ExitCode.NOT_FOUND,
                suggestion="Query may have expired or ID is invalid",
            )
        else:
            output_error("STATUS_ERROR", "E1002", str(e), ExitCode.GENERAL_ERROR)


def cmd_query_cancel(args: argparse.Namespace) -> None:
    """Cancel a running query."""
    config = get_config(args)
    validate_config(config, ["host", "token"])

    client = get_client(config)

    try:
        client.statement_execution.cancel_execution(args.query_id)
        output_json(
            {
                "query_id": args.query_id,
                "action": "cancel_requested",
                "message": "Cancellation requested - poll status to confirm",
            }
        )
    except Exception as e:
        if "404" in str(e):
            output_error(
                "NOT_FOUND",
                "E5003",
                f"Query not found: {args.query_id}",
                ExitCode.NOT_FOUND,
            )
        else:
            output_error("CANCEL_ERROR", "E1003", str(e), ExitCode.GENERAL_ERROR)


def cmd_warehouses(args: argparse.Namespace) -> None:
    """List SQL warehouses."""
    config = get_config(args)
    validate_config(config, ["host", "token"])

    client = get_client(config)

    try:
        warehouses = list(client.warehouses.list())
        result = {
            "warehouses": [
                {
                    "id": w.id,
                    "name": w.name,
                    "state": w.state.value if w.state else "UNKNOWN",
                    "size": w.cluster_size,
                    "auto_stop_mins": w.auto_stop_mins,
                }
                for w in warehouses
            ]
        }
        output_json(result)
    except Exception as e:
        output_error("LIST_ERROR", "E1004", str(e), ExitCode.GENERAL_ERROR)


def cmd_config_show(args: argparse.Namespace) -> None:
    """Show resolved configuration."""
    config = get_config(args)

    # Mask token
    masked_config = config.copy()
    if masked_config.get("token"):
        token = masked_config["token"]
        if len(token) > TOKEN_MASK_LENGTH:
            masked_config["token"] = f"{token[:TOKEN_MASK_LENGTH]}...****"
        else:
            masked_config["token"] = "****"

    # Add source information
    result = {}
    for key, value in masked_config.items():
        result[key] = value
        # Determine source
        if hasattr(args, key.replace("_id", "")) and getattr(args, key.replace("_id", ""), None):
            result[f"{key}_source"] = f"flag:--{key.replace('_', '-')}"
        elif os.environ.get(f"DATABRICKS_{key.upper()}"):
            result[f"{key}_source"] = f"env:DATABRICKS_{key.upper()}"
        else:
            result[f"{key}_source"] = "context or default"

    output_json(result)


def cmd_config_test(args: argparse.Namespace) -> None:
    """Test configuration and connection."""
    config = get_config(args)
    validate_config(config, ["host", "token"])

    client = get_client(config)

    try:
        start = time.time()
        user = client.current_user.me()
        latency = int((time.time() - start) * 1000)

        result = {
            "valid": True,
            "host": config["host"],
            "user": user.user_name,
            "latency_ms": latency,
        }

        if config.get("warehouse_id"):
            try:
                warehouse = client.warehouses.get(config["warehouse_id"])
                result["warehouse_id"] = config["warehouse_id"]
                result["warehouse_name"] = warehouse.name
                result["warehouse_state"] = warehouse.state.value if warehouse.state else "UNKNOWN"
            except Exception:
                result["warehouse_id"] = config["warehouse_id"]
                result["warehouse_error"] = "Could not verify warehouse"

        output_json(result)

    except Exception as e:
        output_error(
            "CONNECTION_ERROR",
            "E3002",
            f"Connection test failed: {e}",
            ExitCode.AUTH_ERROR,
            suggestion="Verify host URL and token are correct",
        )


def cmd_schema(args: argparse.Namespace) -> None:
    """Output JSON schema for all commands."""
    schema = {
        "name": "databricks-sql-cli",
        "version": "0.1.0",
        "commands": {
            "query": {
                "description": "Execute SQL query (hybrid mode: waits 10s, then returns query_id if still running)",
                "parameters": {
                    "warehouse": {
                        "type": "string",
                        "required": True,
                        "env": "DATABRICKS_WAREHOUSE_ID",
                    },
                    "sql": {"type": "string", "required_unless": ["sql-file", "sql-stdin"]},
                    "sql-file": {"type": "string", "description": "Path to SQL file"},
                    "sql-stdin": {"type": "boolean", "description": "Read SQL from stdin"},
                    "params": {"type": "object", "description": "Named parameters as JSON"},
                    "timeout-ms": {"type": "integer", "default": 300000},
                    "max-rows": {"type": "integer", "default": 10000},
                    "format": {
                        "type": "string",
                        "enum": ["json", "csv"],
                        "default": "json",
                        "description": "Output format: json (stdout) or csv (file)",
                    },
                    "output-dir": {
                        "type": "string",
                        "description": "Directory for CSV output (required with --format=csv)",
                    },
                    "async": {
                        "type": "boolean",
                        "default": False,
                        "description": "Return immediately with query_id",
                    },
                    "wait": {
                        "type": "boolean",
                        "default": False,
                        "description": "Wait indefinitely for query completion",
                    },
                },
                "modes": {
                    "default": "Hybrid - waits 10s, returns query_id if still running",
                    "--async": "Returns immediately with query_id",
                    "--wait": "Waits indefinitely until query completes",
                },
            },
            "query-status": {
                "description": "Get status of async query",
                "parameters": {
                    "query-id": {"type": "string", "required": True},
                },
            },
            "query-cancel": {
                "description": "Cancel running query",
                "parameters": {
                    "query-id": {"type": "string", "required": True},
                },
            },
            "warehouses": {
                "description": "List SQL warehouses",
                "parameters": {},
            },
            "config-show": {
                "description": "Show resolved configuration",
                "parameters": {},
            },
            "config-test": {
                "description": "Test connection",
                "parameters": {},
            },
        },
        "global_parameters": {
            "host": {"type": "string", "env": "DATABRICKS_HOST"},
            "token": {"type": "string", "env": "DATABRICKS_TOKEN"},
            "token-file": {"type": "string", "description": "Path to token file"},
            "warehouse": {"type": "string", "env": "DATABRICKS_WAREHOUSE_ID"},
            "catalog": {"type": "string", "env": "DATABRICKS_CATALOG"},
            "schema": {"type": "string", "env": "DATABRICKS_SCHEMA"},
            "context": {"type": "object", "description": "JSON blob with all config"},
        },
        "exit_codes": {
            "0": "Success",
            "1": "General error",
            "2": "Invalid arguments",
            "3": "Authentication error",
            "4": "Authorization error",
            "5": "Resource not found",
            "6": "Conflict",
            "7": "Rate limited",
            "8": "Partial success",
            "9": "Cancelled",
            "10": "Timeout",
        },
    }
    output_json(schema)


def add_global_args(parser: argparse.ArgumentParser) -> None:
    """Add global arguments to parser."""
    parser.add_argument("--host", help="Databricks workspace URL")
    parser.add_argument("--token", help="Personal access token (prefer env var)")
    parser.add_argument("--token-file", help="Path to file containing token")
    parser.add_argument("--warehouse", help="SQL warehouse ID")
    parser.add_argument("--catalog", help="Default catalog")
    parser.add_argument("--schema", help="Default schema")
    parser.add_argument("--context", help="JSON blob with all config")


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        prog="databricks-sql-cli",
        description="Agent-native Databricks SQL CLI",
    )

    # Global flags
    parser.add_argument(
        "--schema-info",
        action="store_true",
        help="Output JSON schema for all commands",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # query command
    query_parser = subparsers.add_parser("query", help="Execute SQL query")
    add_global_args(query_parser)
    query_parser.add_argument("--sql", help="SQL query string")
    query_parser.add_argument("--sql-file", help="Path to SQL file")
    query_parser.add_argument("--sql-stdin", action="store_true", help="Read SQL from stdin")
    query_parser.add_argument("--params", help="Named parameters as JSON")
    query_parser.add_argument("--timeout-ms", type=int, default=300000, help="Query timeout in ms")
    query_parser.add_argument("--max-rows", type=int, default=10000, help="Max rows to return")
    query_parser.add_argument(
        "--format",
        choices=["json", "csv"],
        default="json",
        help="Output format: json (default, to stdout) or csv (requires --output-dir)",
    )
    query_parser.add_argument(
        "--output-dir",
        help="Directory for CSV output file (required with --format=csv)",
    )
    query_parser.add_argument(
        "--async", dest="async_exec", action="store_true", help="Return immediately with query_id"
    )
    query_parser.add_argument(
        "--wait", action="store_true", help="Wait indefinitely for query completion"
    )
    query_parser.set_defaults(func=cmd_query)

    # query-status command
    status_parser = subparsers.add_parser("query-status", help="Get query status")
    add_global_args(status_parser)
    status_parser.add_argument("--query-id", required=True, help="Query ID")
    status_parser.set_defaults(func=cmd_query_status)

    # query-cancel command
    cancel_parser = subparsers.add_parser("query-cancel", help="Cancel query")
    add_global_args(cancel_parser)
    cancel_parser.add_argument("--query-id", required=True, help="Query ID")
    cancel_parser.set_defaults(func=cmd_query_cancel)

    # warehouses command
    wh_parser = subparsers.add_parser("warehouses", help="List warehouses")
    add_global_args(wh_parser)
    wh_parser.set_defaults(func=cmd_warehouses)

    # config-show command
    cfg_show_parser = subparsers.add_parser("config-show", help="Show config")
    add_global_args(cfg_show_parser)
    cfg_show_parser.set_defaults(func=cmd_config_show)

    # config-test command
    cfg_test_parser = subparsers.add_parser("config-test", help="Test connection")
    add_global_args(cfg_test_parser)
    cfg_test_parser.set_defaults(func=cmd_config_test)

    args = parser.parse_args()

    # Handle --schema-info
    if args.schema_info:
        cmd_schema(args)
        return

    # No command provided
    if not args.command:
        output_error(
            "INVALID_ARGUMENT",
            "E2000",
            "No command specified",
            ExitCode.INVALID_ARGUMENTS,
            suggestion="Use --help to see available commands or --schema-info for JSON schema",
        )

    # Execute command
    args.func(args)


if __name__ == "__main__":
    main()
