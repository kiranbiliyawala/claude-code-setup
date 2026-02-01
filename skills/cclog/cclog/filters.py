"""Filter system for streaming conversation records."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import datetime

from cclog.models import (
    AssistantRecord,
    ConversationRecord,
    ToolUseBlock,
    UserRecord,
)


@dataclass
class MessageFilter:
    """Filter criteria for messages.

    All filters are optional. When multiple filters are set,
    they are combined with AND logic.
    """

    # Role filter: "user", "assistant", or None for all
    role: str | None = None

    # Content type filter: "thinking", "text", "tool_use", "tool_result"
    content_type: str | None = None

    # Tool name filter: only messages containing this tool
    tool_name: str | None = None

    # Time range filter
    after: datetime | None = None
    before: datetime | None = None

    # Pagination
    limit: int | None = None
    offset: int = 0

    # Valid values for validation
    _valid_roles: tuple[str, ...] = field(default=("user", "assistant"), init=False, repr=False)
    _valid_content_types: tuple[str, ...] = field(
        default=("thinking", "text", "tool_use", "tool_result"), init=False, repr=False
    )


def matches_role(record: ConversationRecord, role: str | None) -> bool:
    """Check if record matches role filter."""
    if role is None:
        return True

    if role == "user":
        return isinstance(record, UserRecord)
    elif role == "assistant":
        return isinstance(record, AssistantRecord)
    return False


def matches_content_type(record: ConversationRecord, content_type: str | None) -> bool:
    """Check if record contains content of the specified type."""
    if content_type is None:
        return True

    if not isinstance(record, (UserRecord, AssistantRecord)):
        return False

    return any(block.type == content_type for block in record.message.get_content_blocks())


def matches_tool_name(record: ConversationRecord, tool_name: str | None) -> bool:
    """Check if record contains a tool_use with the specified name."""
    if tool_name is None:
        return True

    if not isinstance(record, (UserRecord, AssistantRecord)):
        return False

    for block in record.message.get_content_blocks():
        if isinstance(block, ToolUseBlock) and block.name == tool_name:
            return True
    return False


def matches_time_range(
    record: ConversationRecord,
    after: datetime | None,
    before: datetime | None,
) -> bool:
    """Check if record timestamp falls within time range."""
    if after is None and before is None:
        return True

    if record.timestamp is None:
        # Records without timestamps don't match time filters
        return False

    if after is not None and record.timestamp < after:
        return False

    return not (before is not None and record.timestamp > before)


def matches_filter(record: ConversationRecord, filter_: MessageFilter) -> bool:
    """Check if a record matches all filter criteria."""
    return (
        matches_role(record, filter_.role)
        and matches_content_type(record, filter_.content_type)
        and matches_tool_name(record, filter_.tool_name)
        and matches_time_range(record, filter_.after, filter_.before)
    )


def apply_filters(
    records: Iterator[ConversationRecord],
    filter_: MessageFilter,
) -> Iterator[ConversationRecord]:
    """Apply filters to a stream of records.

    Filters are applied in streaming fashion to avoid loading
    all records into memory. Pagination (offset/limit) is also
    applied during streaming.

    Args:
        records: Iterator of conversation records
        filter_: Filter criteria to apply

    Yields:
        Records matching all filter criteria
    """
    count = 0
    yielded = 0

    for record in records:
        if not matches_filter(record, filter_):
            continue

        count += 1

        # Skip records before offset
        if count <= filter_.offset:
            continue

        yield record
        yielded += 1

        # Stop after limit is reached
        if filter_.limit is not None and yielded >= filter_.limit:
            break
