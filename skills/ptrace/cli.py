"""
CLI for ptrace - Playwright Trace Inspector for AI Agents.

This module provides the command-line interface using argparse with subcommands.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from ptrace import __version__
from ptrace.archive import TraceArchive
from ptrace.commands import actions, console, correlate, errors, events, info, network, screenshot
from ptrace.index import EventIndex

# Exit codes
EXIT_SUCCESS = 0
EXIT_NO_RESULTS = 1
EXIT_INVALID_ARGS = 2
EXIT_FILE_NOT_FOUND = 3
EXIT_PARSE_ERROR = 4


def main(argv: list[str] | None = None) -> int:
    """
    Main entry point for the CLI.

    Args:
        argv: Command-line arguments (default: sys.argv[1:])

    Returns:
        Exit code
    """
    parser = create_parser()
    args = parser.parse_args(argv)

    # Handle --help-json
    if args.help_json:
        output_help_json(parser)
        return EXIT_SUCCESS

    # Handle no command
    if not hasattr(args, "func"):
        parser.print_help()
        return EXIT_SUCCESS

    # Open trace file
    try:
        archive = TraceArchive(args.trace_file)
    except FileNotFoundError:
        _error(f"Trace file not found: {args.trace_file}")
        return EXIT_FILE_NOT_FOUND
    except Exception as e:
        _error(f"Failed to open trace file: {e}")
        return EXIT_PARSE_ERROR

    # Build index
    try:
        index = EventIndex(archive)
    except Exception as e:
        _error(f"Failed to parse trace: {e}")
        archive.close()
        return EXIT_PARSE_ERROR

    # Run command
    try:
        exit_code = args.func(index, args)
    except Exception as e:
        _error(f"Command failed: {e}")
        exit_code = EXIT_PARSE_ERROR
    finally:
        archive.close()

    return exit_code


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser with all subcommands."""
    parser = argparse.ArgumentParser(
        prog="ptrace",
        description="Playwright Trace Inspector for AI Agents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exit Codes:
  0  Success (results found)
  1  No results found
  2  Invalid arguments
  3  Trace file not found
  4  Trace parse error
  5  Index out of range

Examples:
  # Get trace summary
  ptrace trace.zip info

  # List all API calls (exclude static assets)
  ptrace trace.zip network --api-only

  # Get failed network requests
  ptrace trace.zip network --status=4xx,5xx

  # Get console errors
  ptrace trace.zip console --level=error

  # Find events around timestamp 5000ms
  ptrace trace.zip correlate --at=5000 --window=500

  # Extract screenshot at error
  ptrace trace.zip screenshot --error --out=error.jpeg

  # Get all errors with context
  ptrace trace.zip errors --context
""",
    )

    parser.add_argument("-V", "--version", action="version", version=f"ptrace {__version__}")
    parser.add_argument(
        "--help-json",
        action="store_true",
        help="Output help as JSON (for machine parsing)",
    )

    # Positional: trace file
    parser.add_argument("trace_file", type=Path, nargs="?", help="Path to trace.zip file")

    # Create subparsers
    subparsers = parser.add_subparsers(title="commands", dest="command")

    # info command
    _add_info_parser(subparsers)

    # events command
    _add_events_parser(subparsers)

    # network command
    _add_network_parser(subparsers)

    # console command
    _add_console_parser(subparsers)

    # actions command
    _add_actions_parser(subparsers)

    # errors command
    _add_errors_parser(subparsers)

    # correlate command
    _add_correlate_parser(subparsers)

    # screenshot command
    _add_screenshot_parser(subparsers)

    return parser


def _add_common_args(parser: argparse.ArgumentParser) -> None:
    """Add common arguments to a subparser."""
    parser.add_argument(
        "--format",
        choices=["json", "jsonl", "table"],
        default="jsonl",
        help="Output format (default: jsonl)",
    )
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    parser.add_argument("--count", action="store_true", help="Output only count of results")
    parser.add_argument(
        "--allow-empty",
        action="store_true",
        help="Exit 0 even when no results found",
    )


def _add_filter_args(parser: argparse.ArgumentParser) -> None:
    """Add common filter arguments to a subparser."""
    parser.add_argument("--after", type=float, help="Events after timestamp (ms)")
    parser.add_argument("--before", type=float, help="Events before timestamp (ms)")
    parser.add_argument("--limit", type=int, help="Limit number of results")
    parser.add_argument("--offset", type=int, help="Skip first N results")
    parser.add_argument("--index", type=int, help="Get single item by index")


def _add_info_parser(subparsers: Any) -> None:
    """Add the info subcommand."""
    parser = subparsers.add_parser(
        "info",
        help="Trace metadata and statistics",
        description="Display trace metadata and event counts as JSON.",
    )
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    parser.set_defaults(func=info.run, format="json", count=False, allow_empty=True)


def _add_events_parser(subparsers: Any) -> None:
    """Add the events subcommand."""
    parser = subparsers.add_parser(
        "events",
        help="All events (normalized, time-ordered)",
        description="List all events from the trace in timestamp order.",
    )
    _add_common_args(parser)
    _add_filter_args(parser)
    parser.add_argument(
        "--type",
        help="Filter by event type (comma-separated: network,console,action,error,screenshot,log)",
    )
    parser.add_argument("--raw", action="store_true", help="Include raw event data")
    parser.set_defaults(func=events.run)


def _add_network_parser(subparsers: Any) -> None:
    """Add the network subcommand."""
    parser = subparsers.add_parser(
        "network",
        help="Network requests/responses",
        description="List network requests and responses.",
    )
    _add_common_args(parser)
    _add_filter_args(parser)

    # Network-specific filters
    parser.add_argument("--method", help="Filter by HTTP method (comma-separated: GET,POST)")
    parser.add_argument(
        "--status",
        help="Filter by status code (e.g., 200, 200-299, 4xx, 5xx)",
    )
    parser.add_argument("--url", help="Filter by URL (case-insensitive substring)")
    parser.add_argument("--url-regex", help="Filter by URL regex")
    parser.add_argument("--content-type", help="Filter by response content-type")
    parser.add_argument(
        "--api-only",
        action="store_true",
        help="Exclude static assets (.js, .css, images, etc.)",
    )

    # Body options
    parser.add_argument("--body", action="store_true", help="Include request and response bodies")
    parser.add_argument("--request-body", action="store_true", help="Include request body only")
    parser.add_argument("--response-body", action="store_true", help="Include response body only")

    parser.set_defaults(func=network.run)


def _add_console_parser(subparsers: Any) -> None:
    """Add the console subcommand."""
    parser = subparsers.add_parser(
        "console",
        help="Console log entries",
        description="List browser console log entries.",
    )
    _add_common_args(parser)
    _add_filter_args(parser)

    # Console-specific filters
    parser.add_argument(
        "--level",
        help="Filter by log level (comma-separated: debug,log,info,warn,error)",
    )
    parser.add_argument("--text", help="Filter by message text (case-insensitive substring)")
    parser.add_argument("--text-regex", help="Filter by message text regex")
    parser.add_argument("--source", help="Filter by source URL (case-insensitive substring)")

    parser.set_defaults(func=console.run)


def _add_actions_parser(subparsers: Any) -> None:
    """Add the actions subcommand."""
    parser = subparsers.add_parser(
        "actions",
        help="Playwright actions (click, fill, etc.)",
        description="List Playwright actions from the trace.",
    )
    _add_common_args(parser)
    _add_filter_args(parser)

    # Action-specific filters
    parser.add_argument(
        "--action",
        help="Filter by action type (comma-separated: click,fill,goto,expect)",
    )
    parser.add_argument("--selector", help="Filter by selector (case-insensitive substring)")
    parser.add_argument("--selector-regex", help="Filter by selector regex")
    parser.add_argument("--failed", action="store_true", help="Only show failed actions")

    parser.set_defaults(func=actions.run)


def _add_errors_parser(subparsers: Any) -> None:
    """Add the errors subcommand."""
    parser = subparsers.add_parser(
        "errors",
        help="Test failures and errors",
        description="Display test failures, console errors, and failed network requests.",
    )
    _add_common_args(parser)
    parser.add_argument(
        "--context",
        action="store_true",
        help="Include context around error (recent actions, console, network)",
    )
    parser.set_defaults(func=errors.run)


def _add_correlate_parser(subparsers: Any) -> None:
    """Add the correlate subcommand."""
    parser = subparsers.add_parser(
        "correlate",
        help="Events correlated by time window",
        description="Find events within a time window around a timestamp.",
    )
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    parser.add_argument(
        "--allow-empty",
        action="store_true",
        help="Exit 0 even when no results found",
    )
    parser.add_argument(
        "--at",
        type=float,
        required=True,
        help="Target timestamp (ms from trace start)",
    )
    parser.add_argument(
        "--window",
        type=float,
        default=500,
        help="Window size in ms (default: 500)",
    )
    parser.set_defaults(func=correlate.run, format="json", count=False)


def _add_screenshot_parser(subparsers: Any) -> None:
    """Add the screenshot subcommand."""
    parser = subparsers.add_parser(
        "screenshot",
        help="Extract screenshot at timestamp",
        description="Extract screenshots from the trace.",
    )
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    parser.add_argument(
        "--allow-empty",
        action="store_true",
        help="Exit 0 even when no results found",
    )
    parser.add_argument(
        "--format",
        choices=["json", "jsonl"],
        default="jsonl",
        help="Output format for listings (default: jsonl)",
    )

    # Selection modes
    parser.add_argument("--list", action="store_true", help="List all available screenshots")
    parser.add_argument("--at", type=float, help="Get screenshot closest to timestamp (ms)")
    parser.add_argument("--index", type=int, help="Get screenshot by index")
    parser.add_argument("--action", type=int, help="Get screenshot at action index")
    parser.add_argument("--error", action="store_true", help="Get screenshot at error time")
    parser.add_argument("--all", action="store_true", help="Export all screenshots")

    # Filter options for --list
    parser.add_argument("--limit", type=int, help="Limit number of results (for --list)")
    parser.add_argument("--offset", type=int, help="Skip first N results (for --list)")

    # Output options
    parser.add_argument("--out", help="Output file or directory path")

    parser.set_defaults(func=screenshot.run)


def output_help_json(parser: argparse.ArgumentParser) -> None:
    """Output help information as JSON for machine parsing."""
    help_data = {
        "name": "ptrace",
        "version": __version__,
        "description": "Playwright Trace Inspector for AI Agents",
        "usage": "ptrace <trace.zip> <command> [options]",
        "commands": [],
        "exit_codes": {
            "0": "Success (results found)",
            "1": "No results found",
            "2": "Invalid arguments",
            "3": "Trace file not found",
            "4": "Trace parse error",
            "5": "Index out of range",
        },
    }

    # Extract command info from subparsers
    commands_info = [
        {
            "name": "info",
            "description": "Trace metadata and statistics",
            "output": "JSON",
        },
        {
            "name": "events",
            "description": "All events (normalized, time-ordered)",
            "output": "JSONL",
            "filters": ["--type", "--after", "--before", "--limit", "--offset", "--index"],
        },
        {
            "name": "network",
            "description": "Network requests/responses",
            "output": "JSONL",
            "filters": [
                "--method",
                "--status",
                "--url",
                "--url-regex",
                "--content-type",
                "--api-only",
                "--body",
                "--request-body",
                "--response-body",
            ],
        },
        {
            "name": "console",
            "description": "Console log entries",
            "output": "JSONL",
            "filters": ["--level", "--text", "--text-regex", "--source"],
        },
        {
            "name": "actions",
            "description": "Playwright actions (click, fill, etc.)",
            "output": "JSONL",
            "filters": ["--action", "--selector", "--selector-regex", "--failed"],
        },
        {
            "name": "errors",
            "description": "Test failures and errors",
            "output": "JSON",
            "filters": ["--context"],
        },
        {
            "name": "correlate",
            "description": "Events correlated by time window",
            "output": "JSON",
            "required": ["--at"],
            "optional": ["--window"],
        },
        {
            "name": "screenshot",
            "description": "Extract screenshot at timestamp",
            "output": "Binary JPEG or JSON",
            "modes": ["--list", "--at", "--index", "--action", "--error", "--all"],
        },
    ]

    help_data["commands"] = commands_info

    json.dump(help_data, sys.stdout, indent=2)
    sys.stdout.write("\n")


def _error(message: str) -> None:
    """Output error message as JSON to stderr."""
    json.dump({"error": message}, sys.stderr)
    sys.stderr.write("\n")


if __name__ == "__main__":
    sys.exit(main())
