"""
JSON and JSONL output formatters.

- JSON: Single object or array (good for small results)
- JSONL: Newline-delimited JSON (good for streaming large results)
"""

from __future__ import annotations

import json
import sys
from collections.abc import Iterator
from typing import IO, Any


def output_json(
    data: Any,
    file: IO[str] = sys.stdout,
    pretty: bool = False,
) -> None:
    """
    Output data as a single JSON object or array.

    Args:
        data: Data to serialize (dict, list, or any JSON-serializable object)
        file: Output file (default: stdout)
        pretty: Whether to pretty-print with indentation
    """
    if pretty:
        json.dump(data, file, indent=2, default=_json_default)
        file.write("\n")
    else:
        json.dump(data, file, separators=(",", ":"), default=_json_default)
        file.write("\n")
    file.flush()


def output_jsonl(
    items: Iterator[Any] | list[Any],
    file: IO[str] = sys.stdout,
    pretty: bool = False,
) -> int:
    """
    Output items as JSONL (newline-delimited JSON).

    Each item is written on its own line as a JSON object.
    This format is streaming-friendly and memory-efficient.

    Args:
        items: Iterable of items to output
        file: Output file (default: stdout)
        pretty: Whether to pretty-print each line (not recommended for JSONL)

    Returns:
        Number of items written
    """
    count = 0
    for item in items:
        if pretty:
            json.dump(item, file, indent=2, default=_json_default)
        else:
            json.dump(item, file, separators=(",", ":"), default=_json_default)
        file.write("\n")
        file.flush()  # Flush each line for streaming
        count += 1
    return count


def _json_default(obj: Any) -> Any:
    """
    Default JSON serializer for objects not serializable by default.

    Handles:
    - float('inf') -> "Infinity"
    - Objects with to_dict() method
    - Dataclasses (via __dict__)
    """
    if obj == float("inf"):
        return "Infinity"
    if obj == float("-inf"):
        return "-Infinity"
    if hasattr(obj, "to_dict"):
        return obj.to_dict()
    if hasattr(obj, "__dict__"):
        return obj.__dict__
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def format_json(data: Any, pretty: bool = False) -> str:
    """
    Format data as JSON string.

    Args:
        data: Data to serialize
        pretty: Whether to pretty-print

    Returns:
        JSON string
    """
    if pretty:
        return json.dumps(data, indent=2, default=_json_default)
    return json.dumps(data, separators=(",", ":"), default=_json_default)
