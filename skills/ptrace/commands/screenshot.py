"""
screenshot command - Extract screenshots from trace.

Output: Binary JPEG data to stdout, or file path when using --out
"""

from __future__ import annotations

import sys
from collections.abc import Iterator
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ptrace.formatters.json import output_json, output_jsonl

if TYPE_CHECKING:
    from argparse import Namespace

    from ptrace.index import EventIndex

# Exit codes
EXIT_SUCCESS = 0
EXIT_NO_RESULTS = 1
EXIT_INDEX_OUT_OF_RANGE = 5


def run(index: EventIndex, args: Namespace) -> int:  # noqa: PLR0911
    """
    Execute the screenshot command.

    Extracts screenshots by timestamp, index, or exports all to directory.

    Args:
        index: EventIndex for the trace
        args: Parsed command-line arguments

    Returns:
        Exit code
    """
    # Handle --list to list all available screenshots
    if args.list:
        return _list_screenshots(index, args)

    # Handle --all to export all screenshots
    if args.all:
        return _export_all(index, args)

    # Handle --action to get screenshot at action time
    if args.action is not None:
        return _screenshot_at_action(index, args)

    # Handle --error to get screenshot at error time
    if args.error:
        return _screenshot_at_error(index, args)

    # Handle timestamp or index
    if args.at is not None:
        return _screenshot_at_timestamp(index, args)

    if args.index is not None:
        return _screenshot_by_index(index, args)

    # No specific request - list screenshots
    return _list_screenshots(index, args)


def _list_screenshots(index: EventIndex, args: Namespace) -> int:
    """List all available screenshots."""
    screenshots = list(index.screenshots())

    if not screenshots and not args.allow_empty:
        return EXIT_NO_RESULTS

    event_dicts = (e.to_dict() for e in screenshots)

    # Apply offset/limit if provided
    if hasattr(args, "offset") and args.offset:
        event_dicts = _skip(event_dicts, args.offset)
    if hasattr(args, "limit") and args.limit:
        event_dicts = _take(event_dicts, args.limit)

    if args.format == "json":
        output_json(list(event_dicts), sys.stdout, pretty=args.pretty)
    else:
        output_jsonl(event_dicts, sys.stdout)

    return EXIT_SUCCESS


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


def _export_all(index: EventIndex, args: Namespace) -> int:
    """Export all screenshots to a directory."""
    screenshots = list(index.screenshots())

    if not screenshots:
        if not args.allow_empty:
            return EXIT_NO_RESULTS
        output_json({"exported": 0, "files": []}, sys.stdout)
        return EXIT_SUCCESS

    # Create output directory
    out_dir = Path(args.out) if args.out else Path(".")
    out_dir.mkdir(parents=True, exist_ok=True)

    exported_files = []
    for i, event in enumerate(screenshots):
        if not event.screenshot:
            continue

        # Generate filename: NNNN_TIMEms.jpeg
        timestamp = int(event.timestamp_ms)
        filename = f"{i:04d}_{timestamp}ms.jpeg"
        filepath = out_dir / filename

        # Extract screenshot data
        data = index.archive.get_resource(event.screenshot.sha1)
        filepath.write_bytes(data)

        exported_files.append(
            {
                "index": i,
                "timestamp_ms": event.timestamp_ms,
                "path": str(filepath),
                "width": event.screenshot.width,
                "height": event.screenshot.height,
            }
        )

    result = {
        "exported": len(exported_files),
        "directory": str(out_dir),
        "files": exported_files,
    }

    output_json(result, sys.stdout, pretty=args.pretty)
    return EXIT_SUCCESS


def _screenshot_at_timestamp(index: EventIndex, args: Namespace) -> int:
    """Get screenshot closest to a timestamp."""
    closest = index.closest_screenshot(args.at)

    if not closest:
        if not args.allow_empty:
            return EXIT_NO_RESULTS
        output_json({"error": "No screenshots found"}, sys.stderr)
        return EXIT_NO_RESULTS

    return _output_screenshot(index, closest, args)


def _screenshot_by_index(index: EventIndex, args: Namespace) -> int:
    """Get screenshot by index."""
    screenshots = list(index.screenshots())

    if args.index < 0 or args.index >= len(screenshots):
        output_json(
            {"error": f"Index {args.index} out of range (0-{len(screenshots) - 1})"},
            sys.stderr,
        )
        return EXIT_INDEX_OUT_OF_RANGE

    return _output_screenshot(index, screenshots[args.index], args)


def _screenshot_at_action(index: EventIndex, args: Namespace) -> int:
    """Get screenshot at action time."""
    actions = list(index.actions())

    if args.action < 0 or args.action >= len(actions):
        output_json(
            {"error": f"Action index {args.action} out of range (0-{len(actions) - 1})"},
            sys.stderr,
        )
        return EXIT_INDEX_OUT_OF_RANGE

    action_event = actions[args.action]
    closest = index.closest_screenshot(action_event.timestamp_ms)

    if not closest:
        if not args.allow_empty:
            return EXIT_NO_RESULTS
        output_json({"error": "No screenshots found"}, sys.stderr)
        return EXIT_NO_RESULTS

    return _output_screenshot(index, closest, args)


def _screenshot_at_error(index: EventIndex, args: Namespace) -> int:
    """Get screenshot at error time."""
    # Get approximate error time (last finite timestamp)
    all_events = list(index.all())
    finite_events = [e for e in all_events if e.timestamp_ms != float("inf")]

    if not finite_events:
        if not args.allow_empty:
            return EXIT_NO_RESULTS
        output_json({"error": "No events found"}, sys.stderr)
        return EXIT_NO_RESULTS

    error_time = finite_events[-1].timestamp_ms
    closest = index.closest_screenshot(error_time)

    if not closest:
        if not args.allow_empty:
            return EXIT_NO_RESULTS
        output_json({"error": "No screenshots found"}, sys.stderr)
        return EXIT_NO_RESULTS

    return _output_screenshot(index, closest, args)


def _output_screenshot(index: EventIndex, event: Any, args: Namespace) -> int:
    """Output a screenshot (to file or stdout)."""
    if not event.screenshot:
        return EXIT_NO_RESULTS

    data = index.archive.get_resource(event.screenshot.sha1)

    if args.out:
        # Write to file
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(data)

        result = {
            "path": str(out_path),
            "timestamp_ms": event.timestamp_ms,
            "width": event.screenshot.width,
            "height": event.screenshot.height,
            "size_bytes": len(data),
        }
        output_json(result, sys.stdout, pretty=args.pretty)
    else:
        # Write binary to stdout
        sys.stdout.buffer.write(data)

    return EXIT_SUCCESS
