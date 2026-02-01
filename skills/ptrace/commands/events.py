"""
events command - List all events in timestamp order.

Output: JSONL stream of normalized events
"""

from __future__ import annotations

import sys
from collections.abc import Iterator
from typing import TYPE_CHECKING, Any

from ptrace.formatters.json import output_json, output_jsonl
from ptrace.formatters.table import output_table

if TYPE_CHECKING:
    from argparse import Namespace

    from ptrace.index import EventIndex

# Exit codes
EXIT_SUCCESS = 0
EXIT_NO_RESULTS = 1


def run(index: EventIndex, args: Namespace) -> int:  # noqa: PLR0911
    """
    Execute the events command.

    Lists all events, optionally filtered by type, time range, etc.

    Args:
        index: EventIndex for the trace
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success, 1 for no results)
    """
    # Handle --index to get single event
    if args.index is not None:
        all_events = list(index.all())
        if args.index < 0 or args.index >= len(all_events):
            output_json(
                {"error": f"Index {args.index} out of range (0-{len(all_events) - 1})"},
                sys.stderr,
            )
            return 5  # EXIT_INDEX_OUT_OF_RANGE
        event = all_events[args.index]
        output_json(event.to_dict(include_raw=args.raw), sys.stdout, pretty=args.pretty)
        return EXIT_SUCCESS

    # Build event iterator with filters
    events = _filter_events(index, args)

    # Convert to dicts
    event_dicts = (e.to_dict(include_raw=args.raw) for e in events)

    # Apply limit/offset
    if args.offset:
        event_dicts = _skip(event_dicts, args.offset)
    if args.limit:
        event_dicts = _take(event_dicts, args.limit)

    # Output based on format
    if args.count:
        count = sum(1 for _ in event_dicts)
        output_json({"count": count}, sys.stdout)
        return EXIT_SUCCESS if count > 0 or args.allow_empty else EXIT_NO_RESULTS

    if args.format == "json":
        events_list = list(event_dicts)
        if not events_list and not args.allow_empty:
            return EXIT_NO_RESULTS
        output_json(events_list, sys.stdout, pretty=args.pretty)
        return EXIT_SUCCESS

    if args.format == "table":
        columns = [
            ("index", "IDX", 5),
            ("timestamp_ms", "TIME", 10),
            ("event_type", "TYPE", 10),
            ("subtype", "SUBTYPE", 10),
        ]
        count = output_table(event_dicts, columns, sys.stdout)
        return EXIT_SUCCESS if count > 0 or args.allow_empty else EXIT_NO_RESULTS

    # Default: JSONL
    count = output_jsonl(event_dicts, sys.stdout)
    return EXIT_SUCCESS if count > 0 or args.allow_empty else EXIT_NO_RESULTS


def _filter_events(index: EventIndex, args: Namespace):
    """Apply filters to event stream."""
    # Start with all events or type-filtered
    if hasattr(args, "type") and args.type:
        types = [t.strip() for t in args.type.split(",")]
        events = (e for e in index.all() if e.event_type in types)
    else:
        events = index.all()

    # Time filters
    if args.after is not None:
        events = (e for e in events if e.timestamp_ms >= args.after)
    if args.before is not None:
        events = (e for e in events if e.timestamp_ms <= args.before)

    return events


def _skip(iterable: Iterator[dict[str, Any]], n: int) -> Iterator[dict[str, Any]]:
    """Skip first n items."""
    for i, item in enumerate(iterable):
        if i >= n:
            yield item


def _take(iterable: Iterator[dict[str, Any]], n: int) -> Iterator[dict[str, Any]]:
    """Take first n items."""
    for i, item in enumerate(iterable):
        if i >= n:
            break
        yield item
