"""
actions command - List Playwright actions.

Output: JSONL stream of action events
"""

from __future__ import annotations

import re
import sys
from collections.abc import Iterator
from typing import TYPE_CHECKING, Any

from ptrace.formatters.json import output_json, output_jsonl
from ptrace.formatters.table import format_actions_table
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
    Execute the actions command.

    Lists action events (click, fill, expect, goto, etc.).

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
    events = _filter_actions(index, args)

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
        events = _filter_actions(index, args)
        event_dicts = (e.to_dict() for e in events)
        if args.offset:
            event_dicts = _skip(event_dicts, args.offset)
        if args.limit:
            event_dicts = _take(event_dicts, args.limit)
        count = format_actions_table(event_dicts, sys.stdout)
        return EXIT_SUCCESS if count > 0 or args.allow_empty else EXIT_NO_RESULTS

    # Default: JSONL
    count = output_jsonl(event_dicts, sys.stdout)
    return EXIT_SUCCESS if count > 0 or args.allow_empty else EXIT_NO_RESULTS


def _get_single(index: EventIndex, args: Namespace) -> int:
    """Get a single action event by index."""
    action_events = list(index.actions())

    if args.index < 0 or args.index >= len(action_events):
        output_json(
            {"error": f"Index {args.index} out of range (0-{len(action_events) - 1})"},
            sys.stderr,
        )
        return EXIT_INDEX_OUT_OF_RANGE

    event = action_events[args.index]
    output_json(event.to_dict(), sys.stdout, pretty=args.pretty)
    return EXIT_SUCCESS


def _filter_actions(index: EventIndex, args: Namespace) -> Iterator[Event]:
    """Apply filters to action events."""
    events = index.actions()

    # Action type filter
    if args.action:
        action_types = [a.strip().lower() for a in args.action.split(",")]
        events = (e for e in events if e.action and e.action.action.lower() in action_types)

    # Selector filter
    if args.selector:
        pattern = args.selector.lower()
        events = (
            e
            for e in events
            if e.action and e.action.selector and pattern in e.action.selector.lower()
        )

    # Selector regex filter
    if args.selector_regex:
        regex = re.compile(args.selector_regex)
        events = (
            e for e in events if e.action and e.action.selector and regex.search(e.action.selector)
        )

    # Failed only filter
    if args.failed:
        events = (e for e in events if e.action and e.action.error)

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
