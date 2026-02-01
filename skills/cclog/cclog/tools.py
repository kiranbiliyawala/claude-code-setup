"""Tool call extraction and pairing logic."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, cast

from cclog.models import (
    AssistantRecord,
    ConversationRecord,
    ToolResultBlock,
    ToolUseBlock,
    UserRecord,
)
from cclog.parser import parse_jsonl


@dataclass
class ToolFilter:
    """Filter criteria for tool calls.

    All filters are optional. When multiple filters are set,
    they are combined with AND logic.
    """

    # Tool name filter
    name: str | None = None

    # Task-specific filters
    subagent_type: str | None = None

    # Status filter: "success", "error", or None for all
    status: str | None = None

    # Pagination
    limit: int | None = None
    offset: int = 0

    # Valid values
    _valid_statuses: tuple[str, ...] = field(default=("success", "error"), init=False, repr=False)


@dataclass
class ToolCallPair:
    """Paired tool_use and tool_result.

    Contains the tool invocation and its result, with metadata
    for filtering and display.
    """

    tool_use_id: str
    name: str
    input: dict[str, Any]
    result_content: str | list[dict[str, Any]] | None
    is_error: bool
    timestamp: datetime | None
    message_uuid: str | None

    # Task-specific fields
    description: str | None = None
    subagent_type: str | None = None

    def to_dict(self, full: bool = False, max_length: int = 500) -> dict[str, Any]:
        """Convert to dict for JSON output.

        Args:
            full: If True, include complete input/output
            max_length: Max length for truncated content (when full=False)
        """
        result: dict[str, Any] = {
            "tool_use_id": self.tool_use_id,
            "name": self.name,
            "is_error": self.is_error,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "message_uuid": self.message_uuid,
        }

        # Add Task-specific fields if present
        if self.description:
            result["description"] = self.description
        if self.subagent_type:
            result["subagent_type"] = self.subagent_type

        if full:
            result["input"] = self.input
            result["result"] = self.result_content
        else:
            # Truncate for display
            result["input"] = _truncate_dict(self.input, max_length)
            result["result"] = _truncate_content(self.result_content, max_length)

        return result

    @property
    def status(self) -> str:
        """Get status string for filtering."""
        return "error" if self.is_error else "success"


def _truncate_dict(d: dict[str, Any], max_length: int) -> dict[str, Any]:
    """Truncate string values in a dict."""
    result: dict[str, Any] = {}
    for key, value in d.items():
        if isinstance(value, str) and len(value) > max_length:
            result[key] = value[:max_length] + "..."
        elif isinstance(value, dict):
            result[key] = _truncate_dict(cast(dict[str, Any], value), max_length)
        else:
            result[key] = value
    return result


def _truncate_content(
    content: str | list[dict[str, Any]] | None, max_length: int
) -> str | list[dict[str, Any]] | None:
    """Truncate tool result content."""
    if content is None:
        return None
    if isinstance(content, str):
        if len(content) > max_length:
            return content[:max_length] + "..."
        return content
    # List of content blocks
    result: list[dict[str, Any]] = []
    for item in content:
        if "text" in item:
            text = item["text"]
            if isinstance(text, str) and len(text) > max_length:
                result.append({**item, "text": text[:max_length] + "..."})
            else:
                result.append(item)
        else:
            result.append(item)
    return result


def extract_tool_calls(
    records: Iterator[ConversationRecord],
) -> Iterator[ToolCallPair]:
    """Extract and pair tool_use with tool_result blocks.

    Tool results appear in user messages following the assistant message
    that made the tool call. We match them by tool_use_id.

    Args:
        records: Iterator of conversation records

    Yields:
        ToolCallPair for each tool invocation with its result
    """
    # Pending tool uses waiting for results
    pending: dict[str, tuple[ToolUseBlock, datetime | None, str | None]] = {}

    for record in records:
        if isinstance(record, AssistantRecord):
            # Collect tool_use blocks
            for block in record.message.get_content_blocks():
                if isinstance(block, ToolUseBlock):
                    pending[block.id] = (block, record.timestamp, record.uuid)

        elif isinstance(record, UserRecord):
            # Match tool_result blocks with pending tool_uses
            for block in record.message.get_content_blocks():
                if isinstance(block, ToolResultBlock) and block.tool_use_id in pending:
                    tool_use, timestamp, message_uuid = pending.pop(block.tool_use_id)
                    yield ToolCallPair(
                        tool_use_id=tool_use.id,
                        name=tool_use.name,
                        input=tool_use.input,
                        result_content=block.content,
                        is_error=block.is_error,
                        timestamp=timestamp,
                        message_uuid=message_uuid,
                        description=tool_use.description,
                        subagent_type=tool_use.subagent_type,
                    )

    # Yield any unmatched tool_uses (calls without results)
    for tool_use, timestamp, message_uuid in pending.values():
        yield ToolCallPair(
            tool_use_id=tool_use.id,
            name=tool_use.name,
            input=tool_use.input,
            result_content=None,
            is_error=False,
            timestamp=timestamp,
            message_uuid=message_uuid,
            description=tool_use.description,
            subagent_type=tool_use.subagent_type,
        )


def matches_tool_filter(tool_call: ToolCallPair, filter_: ToolFilter) -> bool:
    """Check if a tool call matches filter criteria."""
    if filter_.name is not None and tool_call.name != filter_.name:
        return False
    if filter_.subagent_type is not None and tool_call.subagent_type != filter_.subagent_type:
        return False
    return not (filter_.status is not None and tool_call.status != filter_.status)


def apply_tool_filter(
    tool_calls: Iterator[ToolCallPair],
    filter_: ToolFilter,
) -> Iterator[ToolCallPair]:
    """Apply filters to tool calls with pagination.

    Args:
        tool_calls: Iterator of tool call pairs
        filter_: Filter criteria

    Yields:
        Tool calls matching criteria
    """
    count = 0
    yielded = 0

    for tool_call in tool_calls:
        if not matches_tool_filter(tool_call, filter_):
            continue

        count += 1

        if count <= filter_.offset:
            continue

        yield tool_call
        yielded += 1

        if filter_.limit is not None and yielded >= filter_.limit:
            break


def get_tools(
    path: str | Path,
    filter_: ToolFilter | None = None,
    full: bool = False,
) -> Iterator[dict[str, Any]]:
    """High-level function to get filtered tool calls from a file.

    Args:
        path: Path to JSONL file
        filter_: Optional filter criteria
        full: Include complete input/output

    Yields:
        Tool call dicts
    """
    records = parse_jsonl(path)
    tool_calls = extract_tool_calls(records)

    if filter_ is not None:
        tool_calls = apply_tool_filter(tool_calls, filter_)

    for tool_call in tool_calls:
        yield tool_call.to_dict(full=full)
