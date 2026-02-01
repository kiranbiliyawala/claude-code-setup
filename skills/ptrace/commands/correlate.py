"""
correlate command - Find events correlated by time window.

Output: JSON object with events grouped by type around a timestamp
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from ptrace.formatters.json import output_json

if TYPE_CHECKING:
    from argparse import Namespace

    from ptrace.index import EventIndex

# Exit codes
EXIT_SUCCESS = 0
EXIT_NO_RESULTS = 1


def run(index: EventIndex, args: Namespace) -> int:
    """
    Execute the correlate command.

    Finds all events within a time window around a given timestamp.

    Args:
        index: EventIndex for the trace
        args: Parsed command-line arguments

    Returns:
        Exit code
    """
    timestamp_ms = args.at
    window_ms = args.window

    # Get correlated events
    result = index.correlate(timestamp_ms, window_ms)

    # Add metadata
    output = {
        "target_timestamp_ms": timestamp_ms,
        "window_ms": window_ms,
        "range": {
            "start_ms": timestamp_ms - window_ms,
            "end_ms": timestamp_ms + window_ms,
        },
        "events": result,
        "counts": {k: len(v) for k, v in result.items()},
    }

    # Check if any events found
    total_events = sum(len(v) for v in result.values())
    if total_events == 0 and not args.allow_empty:
        return EXIT_NO_RESULTS

    output_json(output, sys.stdout, pretty=args.pretty)
    return EXIT_SUCCESS
