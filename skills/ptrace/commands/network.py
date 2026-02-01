"""
network command - List network requests/responses.

Output: JSONL stream of network events
"""

from __future__ import annotations

import re
import sys
from collections.abc import Callable, Iterator
from typing import TYPE_CHECKING, Any

from ptrace.formatters.json import output_json, output_jsonl
from ptrace.formatters.table import format_network_table
from ptrace.models import Event

if TYPE_CHECKING:
    from argparse import Namespace

    from ptrace.index import EventIndex

# Exit codes
EXIT_SUCCESS = 0
EXIT_NO_RESULTS = 1
EXIT_INDEX_OUT_OF_RANGE = 5

# Static asset extensions to filter out with --api-only
STATIC_EXTENSIONS = (
    ".js",
    ".css",
    ".map",
    ".svg",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".ico",
    ".woff",
    ".woff2",
    ".ttf",
    ".eot",
)


def run(index: EventIndex, args: Namespace) -> int:
    """
    Execute the network command.

    Lists network events, optionally filtered by method, status, URL, etc.

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
    events = _filter_network(index, args)

    # Convert to output format
    event_dicts = (_to_output_dict(e, args) for e in events)

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
        # Re-generate dicts for table (can't reuse generator)
        events = _filter_network(index, args)
        event_dicts = (_to_output_dict(e, args) for e in events)
        if args.offset:
            event_dicts = _skip(event_dicts, args.offset)
        if args.limit:
            event_dicts = _take(event_dicts, args.limit)
        count = format_network_table(event_dicts, sys.stdout)
        return EXIT_SUCCESS if count > 0 or args.allow_empty else EXIT_NO_RESULTS

    # Default: JSONL
    count = output_jsonl(event_dicts, sys.stdout)
    return EXIT_SUCCESS if count > 0 or args.allow_empty else EXIT_NO_RESULTS


def _get_single(index: EventIndex, args: Namespace) -> int:
    """Get a single network event by index."""
    network_events = list(index.network())

    if args.index < 0 or args.index >= len(network_events):
        output_json(
            {"error": f"Index {args.index} out of range (0-{len(network_events) - 1})"},
            sys.stderr,
        )
        return EXIT_INDEX_OUT_OF_RANGE

    event = network_events[args.index]
    output_dict = _to_output_dict(event, args)
    output_json(output_dict, sys.stdout, pretty=args.pretty)
    return EXIT_SUCCESS


def _filter_network(index: EventIndex, args: Namespace) -> Iterator[Event]:
    """Apply filters to network events."""
    events = index.network()

    # Method filter
    if args.method:
        methods = [m.strip().upper() for m in args.method.split(",")]
        events = (e for e in events if e.network and e.network.method in methods)

    # Status filter
    if args.status:
        status_filter = _parse_status_filter(args.status)
        events = (e for e in events if e.network and status_filter(e.network.status))

    # URL filter
    if args.url:
        pattern = args.url.lower()
        events = (e for e in events if e.network and pattern in e.network.url.lower())

    # URL regex filter
    if args.url_regex:
        regex = re.compile(args.url_regex)
        events = (e for e in events if e.network and regex.search(e.network.url))

    # Content-type filter
    if args.content_type:
        ct_pattern = args.content_type.lower()
        events = (
            e for e in events if e.network and ct_pattern in e.network.response_content_type.lower()
        )

    # API-only filter (exclude static assets)
    if args.api_only:
        events = (
            e
            for e in events
            if e.network
            and not e.network.url.endswith(STATIC_EXTENSIONS)
            and ":5173" not in e.network.url  # Exclude Vite dev server
        )

    # Time filters
    if args.after is not None:
        events = (e for e in events if e.timestamp_ms >= args.after)
    if args.before is not None:
        events = (e for e in events if e.timestamp_ms <= args.before)

    return events


def _parse_status_filter(status_str: str) -> Callable[[int], bool]:
    """
    Parse status filter string into a predicate function.

    Supports:
    - Single status: "200"
    - Range: "200-299"
    - Class: "4xx", "5xx"
    - Comma-separated: "200,201,404"
    """
    parts = [p.strip() for p in status_str.split(",")]
    predicates: list[Callable[[int], bool]] = []

    for part in parts:
        if "-" in part:
            # Range
            start, end = part.split("-")
            start_int, end_int = int(start), int(end)
            predicates.append(lambda s, lo=start_int, hi=end_int: lo <= s <= hi)
        elif part.endswith("xx"):
            # Class (e.g., 4xx, 5xx)
            base = int(part[0]) * 100
            predicates.append(lambda s, b=base: b <= s < b + 100)
        else:
            # Single status
            status_int = int(part)
            predicates.append(lambda s, target=status_int: s == target)

    return lambda status: any(p(status) for p in predicates)


def _to_output_dict(event: Event, args: Namespace) -> dict[str, Any]:
    """Convert event to output dict, respecting body flags."""
    base = event.to_dict()

    # Handle body flags
    if not args.body and "network" in base:
        # By default, don't include bodies (they can be large)
        if not args.request_body:
            base["network"]["request_body"] = None
        if not args.response_body:
            base["network"]["response_body"] = None

    # If only specific body requested
    if args.request_body and not args.response_body and "network" in base:
        base["network"]["response_body"] = None
    if args.response_body and not args.request_body and "network" in base:
        base["network"]["request_body"] = None

    return base


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
