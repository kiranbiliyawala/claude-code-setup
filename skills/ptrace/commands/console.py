"""
console command - List console log entries.

Output: JSONL stream of console events
"""

from __future__ import annotations

import re
import sys
from collections.abc import Iterator
from typing import TYPE_CHECKING, Any

from ptrace.formatters.json import output_json, output_jsonl
from ptrace.formatters.table import format_console_table
from ptrace.models import Event

if TYPE_CHECKING:
    from argparse import Namespace

    from ptrace.index import EventIndex

# Exit codes
EXIT_SUCCESS = 0
EXIT_NO_RESULTS = 1
EXIT_INDEX_OUT_OF_RANGE = 5


def run(index: EventIndex, args: Namespace) -> int:
    """
    Execute the console command.

    Lists console log events, optionally filtered by level, text, etc.

    Args:
        index: EventIndex for the trace
        args: Parsed command-line arguments

    Returns:
        Exit code
    """
    # Handle --index for single item retrieval
    if args.index is not None:
        return _get_single(index, args)

    # Build event iterator with filters
    events = _filter_console(index, args)

    # Convert to output format
    event_dicts = (e.to_dict() for e in events)

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
        events = _filter_console(index, args)
        event_dicts = (e.to_dict() for e in events)
        if args.offset:
            event_dicts = _skip(event_dicts, args.offset)
        if args.limit:
            event_dicts = _take(event_dicts, args.limit)
        count = format_console_table(event_dicts, sys.stdout)
        return EXIT_SUCCESS if count > 0 or args.allow_empty else EXIT_NO_RESULTS

    # Default: JSONL
    count = output_jsonl(event_dicts, sys.stdout)
    return EXIT_SUCCESS if count > 0 or args.allow_empty else EXIT_NO_RESULTS


def _get_single(index: EventIndex, args: Namespace) -> int:
    """Get a single console event by index."""
    console_events = list(index.console())

    if args.index < 0 or args.index >= len(console_events):
        output_json(
            {"error": f"Index {args.index} out of range (0-{len(console_events) - 1})"},
            sys.stderr,
        )
        return EXIT_INDEX_OUT_OF_RANGE

    event = console_events[args.index]
    output_json(event.to_dict(), sys.stdout, pretty=args.pretty)
    return EXIT_SUCCESS


def _filter_console(index: EventIndex, args: Namespace) -> Iterator[Event]:
    """Apply filters to console events."""
    events = index.console()

    # Level filter
    if args.level:
        levels = [lv.strip().lower() for lv in args.level.split(",")]
        events = (e for e in events if e.console and e.console.level in levels)

    # Text filter
    if args.text:
        pattern = args.text.lower()
        events = (e for e in events if e.console and pattern in e.console.text.lower())

    # Text regex filter
    if args.text_regex:
        regex = re.compile(args.text_regex)
        events = (e for e in events if e.console and regex.search(e.console.text))

    # Source filter
    if args.source:
        pattern = args.source.lower()
        events = (e for e in events if e.console and pattern in e.console.source_url.lower())

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
