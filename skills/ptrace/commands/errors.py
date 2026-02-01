"""
errors command - Display test failures and errors.

Output: JSON object with error details and context
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Any

from ptrace.formatters.json import output_json, output_jsonl
from ptrace.formatters.table import format_errors_table

if TYPE_CHECKING:
    from argparse import Namespace

    from ptrace.index import EventIndex
    from ptrace.models import Event

# Exit codes
EXIT_SUCCESS = 0
EXIT_NO_RESULTS = 1

# HTTP status threshold for failed requests
HTTP_ERROR_THRESHOLD = 400  # noqa: PLR2004


def run(index: EventIndex, args: Namespace) -> int:
    """
    Execute the errors command.

    Shows test failures, console errors, and failed network requests.

    Args:
        index: EventIndex for the trace
        args: Parsed command-line arguments

    Returns:
        Exit code
    """
    result: dict[str, Any] = {
        "has_errors": False,
        "test_failure": None,
        "console_errors": [],
        "failed_requests": [],
    }

    # Get test failure (from test.trace)
    test_errors = list(index.errors())
    if test_errors:
        result["has_errors"] = True
        result["test_failure"] = test_errors[0].to_dict()

    # Get console errors
    console_errors = [
        e.to_dict() for e in index.console() if e.console and e.console.level == "error"
    ]
    if console_errors:
        result["has_errors"] = True
        result["console_errors"] = console_errors

    # Get failed network requests (4xx, 5xx)
    failed_requests = [
        e.to_dict()
        for e in index.network()
        if e.network and e.network.status >= HTTP_ERROR_THRESHOLD
    ]
    if failed_requests:
        result["has_errors"] = True
        result["failed_requests"] = failed_requests

    # Include context if requested
    if args.context and result["test_failure"]:
        result["context"] = _get_error_context(index, test_errors[0])

    # Check if anything was found
    if not result["has_errors"] and not args.allow_empty:
        return EXIT_NO_RESULTS

    # Output based on format
    if args.format == "table":
        # For table format, just list the errors
        all_errors = test_errors + [
            e for e in index.console() if e.console and e.console.level == "error"
        ]
        event_dicts = (e.to_dict() for e in all_errors)
        count = format_errors_table(event_dicts, sys.stdout)
        return EXIT_SUCCESS if count > 0 or args.allow_empty else EXIT_NO_RESULTS

    if args.format == "jsonl":
        # JSONL: output each error as separate line
        items = []
        if result["test_failure"]:
            items.append({"type": "test_failure", **result["test_failure"]})
        for ce in result["console_errors"]:
            items.append({"type": "console_error", **ce})
        for fr in result["failed_requests"]:
            items.append({"type": "failed_request", **fr})
        count = output_jsonl(items, sys.stdout)
        return EXIT_SUCCESS if count > 0 or args.allow_empty else EXIT_NO_RESULTS

    # Default: JSON object
    output_json(result, sys.stdout, pretty=args.pretty)
    return EXIT_SUCCESS


def _get_error_context(index: EventIndex, error_event: Event) -> dict[str, Any]:
    """
    Get context around an error for debugging.

    Includes:
    - Recent actions before the error
    - Console logs around the error
    - Closest screenshot
    - Recent network calls
    """
    # Use the last finite timestamp we have since error timestamp is inf
    all_events = list(index.all())
    finite_events = [e for e in all_events if e.timestamp_ms != float("inf")]

    if not finite_events:
        return {}

    # Use the last event's timestamp as the "error time"
    error_time = finite_events[-1].timestamp_ms

    context: dict[str, Any] = {
        "approximate_error_time_ms": error_time,
    }

    # Get last 5 actions before error
    all_actions = [e for e in index.actions() if e.timestamp_ms != float("inf")]
    context["recent_actions"] = [e.to_dict() for e in all_actions[-5:]]

    # Get console logs in the last 2 seconds
    recent_console = [
        e.to_dict() for e in index.console() if error_time - 2000 <= e.timestamp_ms <= error_time
    ]
    context["recent_console"] = recent_console

    # Get closest screenshot
    closest = index.closest_screenshot(error_time)
    if closest:
        context["closest_screenshot"] = closest.to_dict()

    # Get recent network calls (last 5)
    all_network = list(index.network())
    context["recent_network"] = [e.to_dict() for e in all_network[-5:]]

    return context
