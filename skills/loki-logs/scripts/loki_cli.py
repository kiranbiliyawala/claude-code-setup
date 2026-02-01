#!/usr/bin/env python3
"""
Agent-native CLI for querying Loki logs via logcli.

Usage:
    python loki_cli.py query --service weave --env stage --preset errors
    python loki_cli.py services --env prod
    python loki_cli.py labels --env stage
    python loki_cli.py stats --service weave --env stage
    python loki_cli.py volume --service weave --env stage
    python loki_cli.py series --service weave --env stage
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
from typing import Any, cast

# Exit codes
EXIT_SUCCESS = 0
EXIT_ERROR = 1
EXIT_INVALID_ARGS = 2
EXIT_CONNECTION_ERROR = 3
EXIT_NOT_FOUND = 5
EXIT_RATE_LIMITED = 7

LOKI_URLS = {
    "stage": "http://loki-read-stg.infra.dreamplug.net",
    "prod": "http://loki-read-prod.infra.dreamplug.net",
}

PRESETS = {
    "errors": '| json | level=~"error|fatal|ERROR|FATAL"',
    "warnings": '| json | level=~"warn|error|fatal|WARN|ERROR|FATAL"',
    "exceptions": '|~ "(?i)(exception|traceback|panic|stack)"',
    "slow": "| json | duration_ms > 1000",
    "5xx": "| json | status_code >= 500",
    "4xx": "| json | status_code >= 400 and status_code < 500",
}

HEALTH_CHECK_FILTERS = """
!= `ELB-HealthChecker`
!~ `GET /health HTTP`
!~ `"url":\\s*"[^"]*\\/health"`
!~ `"operation_type":\\s*".*health_check"`
!~ `"operation_name":\\s*".*health_check"`
!~ `"event":\\s*"Request (started|completed)"`
!~ `"event":\\s*"operation_(started|completed)"`
!~ `"event":\\s*"Performing fresh health checks"`
""".strip().replace("\n", " ")

# Schema for introspection
SCHEMA = {
    "name": "loki-cli",
    "version": "2.0.0",
    "description": "Agent-native CLI for querying Loki logs via logcli",
    "commands": {
        "query": {
            "description": "Query logs from Loki",
            "parameters": {
                "env": {
                    "type": "string",
                    "required": True,
                    "enum": ["stage", "prod"],
                    "description": "Environment to query",
                },
                "service": {
                    "type": "string",
                    "required": False,
                    "description": "Service name (subsystemName label)",
                },
                "logql": {
                    "type": "string",
                    "required": False,
                    "description": "Raw LogQL query (alternative to --service)",
                },
                "query-file": {
                    "type": "string",
                    "required": False,
                    "description": "Path to file containing LogQL query (avoids shell escaping issues)",
                },
                "since": {
                    "type": "string",
                    "required": False,
                    "default": "10m",
                    "description": "Time range (e.g., 5m, 1h, 24h)",
                },
                "limit": {
                    "type": "integer",
                    "required": False,
                    "default": 100,
                    "description": "Max entries to return",
                },
                "filter": {
                    "type": "string",
                    "required": False,
                    "description": "Text filter (adds |= 'text')",
                },
                "preset": {
                    "type": "string",
                    "required": False,
                    "enum": ["errors", "warnings", "exceptions", "slow", "5xx", "4xx"],
                    "description": "Preset query filter",
                },
                "exclude-health": {
                    "type": "boolean",
                    "required": False,
                    "default": False,
                    "description": "Exclude health check logs",
                },
                "parallel": {
                    "type": "boolean",
                    "required": False,
                    "default": False,
                    "description": "Use parallel queries for large time ranges",
                },
                "format": {
                    "type": "string",
                    "required": False,
                    "default": "json",
                    "enum": ["json", "human"],
                    "description": "Output format",
                },
            },
        },
        "services": {
            "description": "List available services",
            "parameters": {
                "env": {
                    "type": "string",
                    "required": True,
                    "enum": ["stage", "prod"],
                    "description": "Environment to query",
                },
                "filter": {
                    "type": "string",
                    "required": False,
                    "description": "Filter service names",
                },
                "format": {
                    "type": "string",
                    "required": False,
                    "default": "json",
                    "enum": ["json", "human"],
                    "description": "Output format",
                },
            },
        },
        "labels": {
            "description": "List labels or label values",
            "parameters": {
                "env": {
                    "type": "string",
                    "required": True,
                    "enum": ["stage", "prod"],
                    "description": "Environment to query",
                },
                "label": {
                    "type": "string",
                    "required": False,
                    "description": "Get values for specific label",
                },
                "format": {
                    "type": "string",
                    "required": False,
                    "default": "json",
                    "enum": ["json", "human"],
                    "description": "Output format",
                },
            },
        },
        "stats": {
            "description": "Get query statistics (bytes, chunks, streams, entries)",
            "parameters": {
                "env": {
                    "type": "string",
                    "required": True,
                    "enum": ["stage", "prod"],
                    "description": "Environment to query",
                },
                "service": {
                    "type": "string",
                    "required": False,
                    "description": "Service name (subsystemName label)",
                },
                "logql": {
                    "type": "string",
                    "required": False,
                    "description": "Raw LogQL query (alternative to --service)",
                },
                "since": {
                    "type": "string",
                    "required": False,
                    "default": "1h",
                    "description": "Time range (e.g., 5m, 1h, 24h)",
                },
                "format": {
                    "type": "string",
                    "required": False,
                    "default": "json",
                    "enum": ["json", "human"],
                    "description": "Output format",
                },
            },
        },
        "volume": {
            "description": "Get log volume aggregation",
            "parameters": {
                "env": {
                    "type": "string",
                    "required": True,
                    "enum": ["stage", "prod"],
                    "description": "Environment to query",
                },
                "service": {
                    "type": "string",
                    "required": False,
                    "description": "Service name (subsystemName label)",
                },
                "logql": {
                    "type": "string",
                    "required": False,
                    "description": "Raw LogQL query (alternative to --service)",
                },
                "since": {
                    "type": "string",
                    "required": False,
                    "default": "1h",
                    "description": "Time range (e.g., 5m, 1h, 24h)",
                },
                "format": {
                    "type": "string",
                    "required": False,
                    "default": "json",
                    "enum": ["json", "human"],
                    "description": "Output format",
                },
            },
        },
        "series": {
            "description": "List log streams matching query",
            "parameters": {
                "env": {
                    "type": "string",
                    "required": True,
                    "enum": ["stage", "prod"],
                    "description": "Environment to query",
                },
                "service": {
                    "type": "string",
                    "required": False,
                    "description": "Service name (subsystemName label)",
                },
                "logql": {
                    "type": "string",
                    "required": False,
                    "description": "Raw LogQL query (alternative to --service)",
                },
                "since": {
                    "type": "string",
                    "required": False,
                    "default": "1h",
                    "description": "Time range (e.g., 5m, 1h, 24h)",
                },
                "format": {
                    "type": "string",
                    "required": False,
                    "default": "json",
                    "enum": ["json", "human"],
                    "description": "Output format",
                },
            },
        },
    },
    "presets": {
        "errors": "Error/fatal level logs",
        "warnings": "Warning+ level logs",
        "exceptions": "Stack traces, panics, exceptions",
        "slow": "Slow requests (>1s)",
        "5xx": "HTTP 5xx server errors",
        "4xx": "HTTP 4xx client errors",
    },
    "environments": {
        "stage": "http://loki-read-stg.infra.dreamplug.net",
        "prod": "http://loki-read-prod.infra.dreamplug.net",
    },
    "exit_codes": {
        "0": "Success",
        "1": "General error",
        "2": "Invalid arguments",
        "3": "Connection error",
        "5": "Resource not found",
        "7": "Rate limited / timeout",
    },
}


def run_logcli(
    env: str,
    args: list[str],
    timeout: float = 60.0,
) -> tuple[int, str, str]:
    """Run logcli command with environment-specific LOKI_ADDR."""
    if env not in LOKI_URLS:
        raise ValueError(f"Invalid environment: {env}. Must be one of: {list(LOKI_URLS.keys())}")

    cmd_env = os.environ.copy()
    cmd_env["LOKI_ADDR"] = LOKI_URLS[env]

    cmd = ["logcli", *args]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=cmd_env,
            check=False,
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return EXIT_RATE_LIMITED, "", "Request timed out"
    except FileNotFoundError:
        return EXIT_ERROR, "", "logcli not found. Install via: brew install logcli"


def build_query(
    service: str | None = None,
    logql: str | None = None,
    preset: str | None = None,
    text_filter: str | None = None,
    exclude_health: bool = False,
) -> str:
    """Build a LogQL query from components."""
    if logql:
        query = logql
    elif service:
        query = f'{{subsystemName="{service}"}}'
    else:
        raise ValueError("Either --service or --logql is required")

    if preset:
        if preset not in PRESETS:
            raise ValueError(f"Invalid preset: {preset}. Available: {list(PRESETS.keys())}")
        query += f" {PRESETS[preset]}"

    if text_filter:
        query += f" |= `{text_filter}`"

    if exclude_health:
        query += f" {HEALTH_CHECK_FILTERS}"

    return query


def parse_jsonl_output(stdout: str) -> list[dict[str, Any]]:
    """Parse JSONL output from logcli."""
    entries = []
    for line in stdout.strip().split("\n"):
        if not line:
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return entries


def parse_size_string(size_str: str) -> int:
    """Parse size string like '2.0MB' or '3.4GB' to bytes."""
    size_str = size_str.strip().upper()
    # Order matters: check longer suffixes first
    multipliers = [
        ("TB", 1024 * 1024 * 1024 * 1024),
        ("GB", 1024 * 1024 * 1024),
        ("MB", 1024 * 1024),
        ("KB", 1024),
        ("B", 1),
    ]
    for suffix, mult in multipliers:
        if size_str.endswith(suffix):
            try:
                return int(float(size_str[: -len(suffix)]) * mult)
            except ValueError:
                return 0
    try:
        return int(float(size_str))
    except ValueError:
        return 0


def parse_stats_output(stdout: str) -> dict[str, Any]:
    """Parse logcli stats output into structured data.

    Input format:
    {
      bytes: 2.0MB
      chunks: 3
      streams: 3
      entries: 2427
    }
    """
    stats = {}
    for line in stdout.strip().split("\n"):
        cleaned_line = line.strip().strip("{}")
        if ":" not in cleaned_line:
            continue
        key, value = cleaned_line.split(":", 1)
        key = key.strip().lower()
        value = value.strip()

        if key == "bytes":
            stats["bytes"] = parse_size_string(value)
            stats["bytes_human"] = value
        elif key in ("chunks", "streams", "entries"):
            try:
                stats[key] = int(value)
            except ValueError:
                stats[key] = value
    return stats


def parse_volume_output(stdout: str) -> list[dict[str, Any]]:
    """Parse logcli volume output into structured data.

    Input format (JSON array):
    [
      {
        "metric": {"subsystemName": "weave"},
        "value": [1767721401.444, "2855426"]
      }
    ]
    """
    try:
        raw = json.loads(stdout.strip())
        volumes = []
        for item in raw:
            metric = item.get("metric", {})
            value = item.get("value", [])
            timestamp = value[0] if len(value) > 0 else None
            bytes_str = value[1] if len(value) > 1 else "0"
            volumes.append(
                {
                    "labels": metric,
                    "timestamp": timestamp,
                    "bytes": int(bytes_str) if bytes_str.isdigit() else 0,
                }
            )
        return volumes
    except (json.JSONDecodeError, TypeError, IndexError):
        return []


def format_output(data: dict[str, Any], human: bool = False) -> str:
    """Format output as JSON or human-readable."""
    if human:
        lines = []
        for entry in data.get("results", {}).get("entries", []):
            ts = entry.get("timestamp", "")
            msg = entry.get("message", "")
            lines.append(f"[{ts}] {msg}")
        return "\n".join(lines) if lines else "No results found."
    return json.dumps(data, indent=2)


def error_response(
    error_type: str,
    code: str,
    message: str,
    suggestion: str | None = None,
    **extra: Any,
) -> dict[str, Any]:
    """Create a structured error response."""
    resp = {
        "error": error_type,
        "code": code,
        "message": message,
    }
    if suggestion:
        resp["suggestion"] = suggestion
    resp.update(extra)
    return resp


def check_connection_error(stderr: str) -> bool:
    """Check if stderr indicates a connection error."""
    connection_patterns = [
        "dial tcp",
        "no such host",
        "connection refused",
        "network is unreachable",
    ]
    return any(p in stderr.lower() for p in connection_patterns)


def cmd_query(args: argparse.Namespace) -> int:  # noqa: PLR0911
    """Execute the query command."""
    try:
        # Handle --query-file: read LogQL from file to avoid shell escaping issues
        logql = args.logql
        if args.query_file:
            try:
                with open(args.query_file) as f:
                    logql = f.read().strip()
            except FileNotFoundError:
                print(
                    json.dumps(
                        error_response(
                            "FILE_NOT_FOUND",
                            "E2003",
                            f"Query file not found: {args.query_file}",
                            suggestion="Ensure the file path is correct",
                        )
                    )
                )
                return EXIT_NOT_FOUND
            except OSError as e:
                print(
                    json.dumps(
                        error_response(
                            "FILE_ERROR",
                            "E2004",
                            f"Cannot read query file: {e}",
                        )
                    )
                )
                return EXIT_ERROR

        if not args.service and not logql:
            print(
                json.dumps(
                    error_response(
                        "VALIDATION_ERROR",
                        "E2001",
                        "Either --service, --logql, or --query-file is required",
                        suggestion="Provide --service=<name>, --logql=<query>, or --query-file=<path>",
                    )
                )
            )
            return EXIT_INVALID_ARGS

        query = build_query(
            service=args.service,
            logql=logql,
            preset=args.preset,
            text_filter=args.filter,
            exclude_health=args.exclude_health,
        )

        logcli_args = [
            "query",
            query,
            f"--limit={args.limit}",
            f"--since={args.since}",
            "-o",
            "jsonl",
            "--quiet",
        ]

        if args.parallel:
            part_prefix = os.path.join(tempfile.gettempdir(), "loki_query_")
            logcli_args.extend(
                [
                    "--parallel-duration=15m",
                    "--parallel-max-workers=4",
                    f"--part-path-prefix={part_prefix}",
                    "--merge-parts",
                ]
            )

        returncode, stdout, stderr = run_logcli(args.env, logcli_args)

        if returncode != 0:
            if check_connection_error(stderr):
                print(
                    json.dumps(
                        error_response(
                            "CONNECTION_ERROR",
                            "E3001",
                            f"Cannot reach Loki at {LOKI_URLS.get(args.env, 'unknown')}",
                            suggestion="Verify you are on the internal network (VPN/VPC)",
                            environment=args.env,
                            details=stderr.strip(),
                        )
                    )
                )
                return EXIT_CONNECTION_ERROR
            if "timeout" in stderr.lower():
                print(
                    json.dumps(
                        error_response(
                            "TIMEOUT_ERROR",
                            "E7001",
                            "Request timed out",
                            suggestion="Try a smaller time range or add more specific filters",
                            environment=args.env,
                        )
                    )
                )
                return EXIT_RATE_LIMITED
            print(
                json.dumps(
                    error_response(
                        "QUERY_ERROR",
                        "E1002",
                        f"Query failed: {stderr.strip()}",
                        query=query,
                    )
                )
            )
            return EXIT_ERROR

        raw_entries = parse_jsonl_output(stdout)

        entries = []
        for entry in raw_entries:
            ts = entry.get("timestamp", "")
            msg = entry.get("line", "")
            labels = entry.get("labels", {})
            entries.append(
                {
                    "timestamp": ts,
                    "message": msg,
                    "labels": labels,
                }
            )

        response = {
            "status": "success",
            "query": query,
            "environment": args.env,
            "results": {
                "total_entries": len(entries),
                "entries": entries,
            },
        }

        print(format_output(response, human=args.format == "human"))
        return EXIT_SUCCESS

    except ValueError as e:
        print(json.dumps(error_response("VALIDATION_ERROR", "E2002", str(e))))
        return EXIT_INVALID_ARGS
    except Exception as e:
        print(json.dumps(error_response("INTERNAL_ERROR", "E1001", str(e))))
        return EXIT_ERROR


def cmd_services(args: argparse.Namespace) -> int:
    """Execute the services command."""
    try:
        logcli_args = ["labels", "subsystemName", "--quiet"]
        returncode, stdout, stderr = run_logcli(args.env, logcli_args)

        if returncode != 0:
            if check_connection_error(stderr):
                print(
                    json.dumps(
                        error_response(
                            "CONNECTION_ERROR",
                            "E3001",
                            f"Cannot reach Loki at {LOKI_URLS.get(args.env, 'unknown')}",
                            suggestion="Verify you are on the internal network (VPN/VPC)",
                            environment=args.env,
                        )
                    )
                )
                return EXIT_CONNECTION_ERROR
            print(json.dumps(error_response("QUERY_ERROR", "E1002", stderr.strip())))
            return EXIT_ERROR

        services = [s.strip().strip('"') for s in stdout.strip().split("\n") if s.strip()]

        if args.filter:
            pattern = args.filter.lower()
            services = [s for s in services if pattern in s.lower()]

        response = {
            "status": "success",
            "environment": args.env,
            "count": len(services),
            "services": sorted(services),
        }

        if args.format == "human":
            print(f"Services in {args.env} ({len(services)} total):")
            for svc in sorted(services):
                print(f"  {svc}")
        else:
            print(json.dumps(response, indent=2))

        return EXIT_SUCCESS

    except Exception as e:
        print(json.dumps(error_response("INTERNAL_ERROR", "E1001", str(e))))
        return EXIT_ERROR


def cmd_labels(args: argparse.Namespace) -> int:  # noqa: PLR0912
    """Execute the labels command."""
    try:
        if args.label:
            logcli_args = ["labels", args.label, "--quiet"]
        else:
            logcli_args = ["labels", "--quiet"]

        returncode, stdout, stderr = run_logcli(args.env, logcli_args)

        if returncode != 0:
            if check_connection_error(stderr):
                print(
                    json.dumps(
                        error_response(
                            "CONNECTION_ERROR",
                            "E3001",
                            f"Cannot reach Loki at {LOKI_URLS.get(args.env, 'unknown')}",
                            suggestion="Verify you are on the internal network (VPN/VPC)",
                            environment=args.env,
                        )
                    )
                )
                return EXIT_CONNECTION_ERROR
            print(json.dumps(error_response("QUERY_ERROR", "E1002", stderr.strip())))
            return EXIT_ERROR

        values = [v.strip().strip('"') for v in stdout.strip().split("\n") if v.strip()]
        sorted_values = sorted(values)

        if args.label:
            if args.format == "human":
                print(f"Values for '{args.label}' in {args.env} ({len(sorted_values)} total):")
                for val in sorted_values:
                    print(f"  {val}")
            else:
                response = {
                    "status": "success",
                    "environment": args.env,
                    "label": args.label,
                    "count": len(sorted_values),
                    "values": sorted_values,
                }
                print(json.dumps(response, indent=2))
        else:  # noqa: PLR5501
            if args.format == "human":
                print(f"Labels in {args.env} ({len(sorted_values)} total):")
                for lbl in sorted_values:
                    print(f"  {lbl}")
            else:
                response = {
                    "status": "success",
                    "environment": args.env,
                    "count": len(sorted_values),
                    "labels": sorted_values,
                }
                print(json.dumps(response, indent=2))

        return EXIT_SUCCESS

    except Exception as e:
        print(json.dumps(error_response("INTERNAL_ERROR", "E1001", str(e))))
        return EXIT_ERROR


def cmd_stats(args: argparse.Namespace) -> int:
    """Execute the stats command."""
    try:
        if not args.service and not args.logql:
            print(
                json.dumps(
                    error_response(
                        "VALIDATION_ERROR",
                        "E2001",
                        "Either --service or --logql is required",
                        suggestion="Provide --service=<name> or --logql=<query>",
                    )
                )
            )
            return EXIT_INVALID_ARGS

        if args.logql:
            query = args.logql
        else:
            query = f'{{subsystemName="{args.service}"}}'

        logcli_args = ["stats", query, f"--since={args.since}"]
        returncode, stdout, stderr = run_logcli(args.env, logcli_args)

        if returncode != 0:
            if check_connection_error(stderr):
                print(
                    json.dumps(
                        error_response(
                            "CONNECTION_ERROR",
                            "E3001",
                            f"Cannot reach Loki at {LOKI_URLS.get(args.env, 'unknown')}",
                            suggestion="Verify you are on the internal network (VPN/VPC)",
                            environment=args.env,
                        )
                    )
                )
                return EXIT_CONNECTION_ERROR
            print(json.dumps(error_response("QUERY_ERROR", "E1002", stderr.strip())))
            return EXIT_ERROR

        stats = parse_stats_output(stdout)

        if args.format == "human":
            print(f"Stats for query '{query}' in {args.env}:")
            print(f"  Bytes: {stats.get('bytes_human', 'N/A')}")
            print(f"  Chunks: {stats.get('chunks', 'N/A')}")
            print(f"  Streams: {stats.get('streams', 'N/A')}")
            print(f"  Entries: {stats.get('entries', 'N/A')}")
        else:
            response = {
                "status": "success",
                "query": query,
                "environment": args.env,
                "stats": stats,
            }
            print(json.dumps(response, indent=2))

        return EXIT_SUCCESS

    except Exception as e:
        print(json.dumps(error_response("INTERNAL_ERROR", "E1001", str(e))))
        return EXIT_ERROR


def cmd_volume(args: argparse.Namespace) -> int:
    """Execute the volume command."""
    try:
        if not args.service and not args.logql:
            print(
                json.dumps(
                    error_response(
                        "VALIDATION_ERROR",
                        "E2001",
                        "Either --service or --logql is required",
                        suggestion="Provide --service=<name> or --logql=<query>",
                    )
                )
            )
            return EXIT_INVALID_ARGS

        if args.logql:
            query = args.logql
        else:
            query = f'{{subsystemName="{args.service}"}}'

        logcli_args = ["volume", query, f"--since={args.since}"]
        returncode, stdout, stderr = run_logcli(args.env, logcli_args)

        if returncode != 0:
            if check_connection_error(stderr):
                print(
                    json.dumps(
                        error_response(
                            "CONNECTION_ERROR",
                            "E3001",
                            f"Cannot reach Loki at {LOKI_URLS.get(args.env, 'unknown')}",
                            suggestion="Verify you are on the internal network (VPN/VPC)",
                            environment=args.env,
                        )
                    )
                )
                return EXIT_CONNECTION_ERROR
            print(json.dumps(error_response("QUERY_ERROR", "E1002", stderr.strip())))
            return EXIT_ERROR

        volumes = parse_volume_output(stdout)
        total_bytes = sum(v.get("bytes", 0) for v in volumes)

        if args.format == "human":
            print(f"Volume for query '{query}' in {args.env}:")
            print(f"  Total bytes: {total_bytes:,}")
            for vol in volumes:
                labels = vol.get("labels", {})
                label_str = ", ".join(f"{k}={v}" for k, v in labels.items())
                print(f"  {label_str}: {vol.get('bytes', 0):,} bytes")
        else:
            response = {
                "status": "success",
                "query": query,
                "environment": args.env,
                "total_bytes": total_bytes,
                "volumes": volumes,
            }
            print(json.dumps(response, indent=2))

        return EXIT_SUCCESS

    except Exception as e:
        print(json.dumps(error_response("INTERNAL_ERROR", "E1001", str(e))))
        return EXIT_ERROR


def cmd_series(args: argparse.Namespace) -> int:
    """Execute the series command."""
    try:
        if not args.service and not args.logql:
            print(
                json.dumps(
                    error_response(
                        "VALIDATION_ERROR",
                        "E2001",
                        "Either --service or --logql is required",
                        suggestion="Provide --service=<name> or --logql=<query>",
                    )
                )
            )
            return EXIT_INVALID_ARGS

        if args.logql:
            query = args.logql
        else:
            query = f'{{subsystemName="{args.service}"}}'

        logcli_args = ["series", query, f"--since={args.since}"]
        returncode, stdout, stderr = run_logcli(args.env, logcli_args)

        if returncode != 0:
            if check_connection_error(stderr):
                print(
                    json.dumps(
                        error_response(
                            "CONNECTION_ERROR",
                            "E3001",
                            f"Cannot reach Loki at {LOKI_URLS.get(args.env, 'unknown')}",
                            suggestion="Verify you are on the internal network (VPN/VPC)",
                            environment=args.env,
                        )
                    )
                )
                return EXIT_CONNECTION_ERROR
            print(json.dumps(error_response("QUERY_ERROR", "E1002", stderr.strip())))
            return EXIT_ERROR

        series_lines = [s.strip() for s in stdout.strip().split("\n") if s.strip()]

        if args.format == "human":
            print(f"Series for query '{query}' ({len(series_lines)} streams):")
            for series in series_lines:
                print(f"  {series}")
        else:
            response = {
                "status": "success",
                "query": query,
                "environment": args.env,
                "count": len(series_lines),
                "series": series_lines,
            }
            print(json.dumps(response, indent=2))

        return EXIT_SUCCESS

    except Exception as e:
        print(json.dumps(error_response("INTERNAL_ERROR", "E1001", str(e))))
        return EXIT_ERROR


def main() -> int:  # noqa: PLR0915
    """Main entry point."""
    # Handle --schema and --capabilities before argparse
    if len(sys.argv) == 2:  # noqa: PLR2004
        if sys.argv[1] == "--schema":
            print(json.dumps(SCHEMA, indent=2))
            return EXIT_SUCCESS
        if sys.argv[1] == "--capabilities":
            commands_dict = cast(dict[str, Any], SCHEMA["commands"])
            envs_dict = cast(dict[str, Any], SCHEMA["environments"])
            capabilities = {
                "commands": list(commands_dict.keys()),
                "features": [
                    "presets",
                    "health-filter",
                    "parallel-queries",
                    "structured-output",
                ],
                "output_formats": ["json", "human"],
                "environments": list(envs_dict.keys()),
            }
            print(json.dumps(capabilities, indent=2))
            return EXIT_SUCCESS

    parser = argparse.ArgumentParser(
        description="Agent-native CLI for querying Loki logs via logcli",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Use --schema for full API schema, --capabilities for feature list",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Query command
    query_parser = subparsers.add_parser("query", help="Query logs from Loki")
    query_parser.add_argument("--env", required=True, choices=["stage", "prod"], help="Environment")
    query_parser.add_argument("--service", help="Service name (subsystemName)")
    query_parser.add_argument("--logql", help="Raw LogQL query")
    query_parser.add_argument(
        "--query-file",
        help="Path to file containing LogQL query (avoids shell escaping)",
    )
    query_parser.add_argument("--since", default="10m", help="Time range (e.g., 5m, 1h, 24h)")
    query_parser.add_argument("--limit", type=int, default=100, help="Max entries to return")
    query_parser.add_argument("--filter", help="Text filter (adds |= 'text')")
    query_parser.add_argument(
        "--preset", choices=list(PRESETS.keys()), help="Use preset query filter"
    )
    query_parser.add_argument(
        "--exclude-health", action="store_true", help="Exclude health check logs"
    )
    query_parser.add_argument(
        "--parallel",
        action="store_true",
        help="Use parallel queries for large time ranges",
    )
    query_parser.add_argument(
        "--format", choices=["json", "human"], default="json", help="Output format"
    )

    # Services command
    services_parser = subparsers.add_parser("services", help="List available services")
    services_parser.add_argument(
        "--env", required=True, choices=["stage", "prod"], help="Environment"
    )
    services_parser.add_argument("--filter", help="Filter service names")
    services_parser.add_argument(
        "--format", choices=["json", "human"], default="json", help="Output format"
    )

    # Labels command
    labels_parser = subparsers.add_parser("labels", help="List labels or label values")
    labels_parser.add_argument(
        "--env", required=True, choices=["stage", "prod"], help="Environment"
    )
    labels_parser.add_argument("--label", help="Get values for specific label")
    labels_parser.add_argument(
        "--format", choices=["json", "human"], default="json", help="Output format"
    )

    # Stats command
    stats_parser = subparsers.add_parser("stats", help="Get query statistics")
    stats_parser.add_argument("--env", required=True, choices=["stage", "prod"], help="Environment")
    stats_parser.add_argument("--service", help="Service name (subsystemName)")
    stats_parser.add_argument("--logql", help="Raw LogQL query")
    stats_parser.add_argument("--since", default="1h", help="Time range (e.g., 5m, 1h, 24h)")
    stats_parser.add_argument(
        "--format", choices=["json", "human"], default="json", help="Output format"
    )

    # Volume command
    volume_parser = subparsers.add_parser("volume", help="Get log volume")
    volume_parser.add_argument(
        "--env", required=True, choices=["stage", "prod"], help="Environment"
    )
    volume_parser.add_argument("--service", help="Service name (subsystemName)")
    volume_parser.add_argument("--logql", help="Raw LogQL query")
    volume_parser.add_argument("--since", default="1h", help="Time range (e.g., 5m, 1h, 24h)")
    volume_parser.add_argument(
        "--format", choices=["json", "human"], default="json", help="Output format"
    )

    # Series command
    series_parser = subparsers.add_parser("series", help="List log streams")
    series_parser.add_argument(
        "--env", required=True, choices=["stage", "prod"], help="Environment"
    )
    series_parser.add_argument("--service", help="Service name (subsystemName)")
    series_parser.add_argument("--logql", help="Raw LogQL query")
    series_parser.add_argument("--since", default="1h", help="Time range (e.g., 5m, 1h, 24h)")
    series_parser.add_argument(
        "--format", choices=["json", "human"], default="json", help="Output format"
    )

    args = parser.parse_args()

    commands = {
        "query": cmd_query,
        "services": cmd_services,
        "labels": cmd_labels,
        "stats": cmd_stats,
        "volume": cmd_volume,
        "series": cmd_series,
    }

    if args.command in commands:
        return commands[args.command](args)

    print(
        json.dumps(
            error_response(
                "INVALID_COMMAND",
                "E2000",
                f"Unknown command: {args.command}",
                suggestion="Use one of: query, services, labels, stats, volume, series",
            )
        )
    )
    return EXIT_INVALID_ARGS


if __name__ == "__main__":
    sys.exit(main())
