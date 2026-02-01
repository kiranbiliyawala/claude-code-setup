"""
Table output formatter for human-readable output.

Used when --format=table is specified.
"""

from __future__ import annotations

import sys
from collections.abc import Iterator
from typing import IO, Any

# Display constants
MAX_URL_LENGTH = 60
MAX_TEXT_LENGTH = 70
MAX_SELECTOR_LENGTH = 50


def output_table(
    items: Iterator[dict[str, Any]] | list[dict[str, Any]],
    columns: list[tuple[str, str, int]],  # (key, header, width)
    file: IO[str] = sys.stdout,
) -> int:
    """
    Output items as a formatted table.

    Args:
        items: Iterable of dicts to display
        columns: List of (key, header, width) tuples
        file: Output file (default: stdout)

    Returns:
        Number of items written
    """
    # Print header
    header = " ".join(h.ljust(w) for _, h, w in columns)
    file.write(header + "\n")
    file.write("-" * len(header) + "\n")

    # Print rows
    count = 0
    for item in items:
        row_parts = []
        for key, _, width in columns:
            value = _get_nested(item, key)
            value_str = _format_value(value, width)
            row_parts.append(value_str.ljust(width))
        file.write(" ".join(row_parts) + "\n")
        count += 1

    file.write(f"\nTotal: {count}\n")
    file.flush()
    return count


def _get_nested(data: dict[str, Any], key: str) -> Any:
    """Get value from nested dict using dot notation."""
    parts = key.split(".")
    value = data
    for part in parts:
        if isinstance(value, dict):
            value = value.get(part, "")
        else:
            return ""
    return value


def _format_value(value: Any, max_width: int) -> str:
    """Format a value for table display, truncating if needed."""
    if value is None:
        return ""

    str_value = str(value)

    # Truncate if too long
    if len(str_value) > max_width:
        return str_value[: max_width - 3] + "..."

    return str_value


def format_network_table(events: Iterator[dict[str, Any]], file: IO[str] = sys.stdout) -> int:
    """Format network events as a table."""
    columns = [
        ("index", "IDX", 5),
        ("timestamp_ms", "TIME", 10),
        ("network.method", "METHOD", 7),
        ("network.url", "URL", 60),
        ("network.status", "STATUS", 6),
        ("network.duration_ms", "DUR", 8),
    ]
    return output_table(events, columns, file)


def format_console_table(events: Iterator[dict[str, Any]], file: IO[str] = sys.stdout) -> int:
    """Format console events as a table."""
    columns = [
        ("index", "IDX", 5),
        ("timestamp_ms", "TIME", 10),
        ("console.level", "LEVEL", 7),
        ("console.text", "MESSAGE", 70),
        ("console.source_url", "SOURCE", 30),
    ]
    return output_table(events, columns, file)


def format_actions_table(events: Iterator[dict[str, Any]], file: IO[str] = sys.stdout) -> int:
    """Format action events as a table."""
    columns = [
        ("index", "IDX", 5),
        ("timestamp_ms", "TIME", 10),
        ("action.action", "ACTION", 12),
        ("action.selector", "SELECTOR", 50),
        ("action.duration_ms", "DUR", 8),
    ]
    return output_table(events, columns, file)


def format_errors_table(events: Iterator[dict[str, Any]], file: IO[str] = sys.stdout) -> int:
    """Format error events as a table."""
    columns = [
        ("index", "IDX", 5),
        ("error.source", "SOURCE", 15),
        ("error.message", "MESSAGE", 80),
    ]
    return output_table(events, columns, file)


def format_screenshots_table(events: Iterator[dict[str, Any]], file: IO[str] = sys.stdout) -> int:
    """Format screenshot events as a table."""
    columns = [
        ("index", "IDX", 5),
        ("timestamp_ms", "TIME", 10),
        ("screenshot.width", "WIDTH", 6),
        ("screenshot.height", "HEIGHT", 6),
        ("screenshot.sha1", "SHA1", 45),
    ]
    return output_table(events, columns, file)
