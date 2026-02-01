"""Timeline event extraction from conversation records."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal

from cclog.models import (
    AssistantRecord,
    ConversationRecord,
    TextBlock,
    ThinkingBlock,
    ToolResultBlock,
    ToolUseBlock,
    UserRecord,
)

EventType = Literal["user_message", "thinking", "text", "tool_use", "tool_result"]


@dataclass
class TimelineEvent:
    """A single event in the conversation timeline.

    Events are extracted from content blocks within messages,
    ordered by timestamp with durations calculated between events.
    """

    event_type: EventType
    timestamp: datetime | None
    message_uuid: str | None

    # Duration to next event in milliseconds
    duration_ms: int | None = None

    # Event-specific content (truncated for display)
    summary: str = ""

    # Tool-specific fields
    tool_name: str | None = None
    tool_use_id: str | None = None
    is_error: bool = False

    # Grouping support
    group_key: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dict for JSON output."""
        result: dict[str, Any] = {
            "event_type": self.event_type,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "message_uuid": self.message_uuid,
            "summary": self.summary,
        }

        if self.duration_ms is not None:
            result["duration_ms"] = self.duration_ms
        if self.tool_name:
            result["tool_name"] = self.tool_name
        if self.tool_use_id:
            result["tool_use_id"] = self.tool_use_id
        if self.is_error:
            result["is_error"] = self.is_error
        if self.group_key:
            result["group_key"] = self.group_key

        return result


@dataclass
class TimelineFilter:
    """Filter criteria for timeline events."""

    after: datetime | None = None
    before: datetime | None = None
    event_types: list[EventType] | None = None
    tool_names: list[str] | None = None
    group_by: str | None = None  # "tool", "event_type", None

    # Pagination
    limit: int | None = None
    offset: int = 0


@dataclass
class TimelineSummary:
    """Summary statistics for a timeline."""

    total_events: int = 0
    total_duration_ms: int | None = None
    events_by_type: dict[str, int] = field(default_factory=lambda: {})
    events_by_tool: dict[str, int] = field(default_factory=lambda: {})
    first_timestamp: datetime | None = None
    last_timestamp: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dict for JSON output."""
        return {
            "total_events": self.total_events,
            "total_duration_ms": self.total_duration_ms,
            "events_by_type": self.events_by_type,
            "events_by_tool": self.events_by_tool,
            "first_timestamp": (self.first_timestamp.isoformat() if self.first_timestamp else None),
            "last_timestamp": (self.last_timestamp.isoformat() if self.last_timestamp else None),
        }


def _truncate(text: str, max_length: int = 100) -> str:
    """Truncate text with ellipsis."""
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."


def _extract_events_from_record(
    record: ConversationRecord,
    group_by: str | None = None,
) -> Iterator[TimelineEvent]:
    """Extract timeline events from a single record."""
    if isinstance(record, UserRecord):
        # User messages as single events
        content_blocks = record.message.get_content_blocks()
        text_parts: list[str] = []
        for block in content_blocks:
            if isinstance(block, TextBlock):
                text_parts.append(block.text)
            elif isinstance(block, ToolResultBlock):
                # Tool results in user messages (from tool execution)
                group_key = None
                if group_by == "event_type":
                    group_key = "tool_result"

                yield TimelineEvent(
                    event_type="tool_result",
                    timestamp=record.timestamp,
                    message_uuid=record.uuid,
                    summary=_truncate(block.content_text),
                    tool_use_id=block.tool_use_id,
                    is_error=block.is_error,
                    group_key=group_key,
                )

        if text_parts:
            group_key = None
            if group_by == "event_type":
                group_key = "user_message"

            yield TimelineEvent(
                event_type="user_message",
                timestamp=record.timestamp,
                message_uuid=record.uuid,
                summary=_truncate(" ".join(text_parts)),
                group_key=group_key,
            )

    elif isinstance(record, AssistantRecord):
        # Assistant messages have multiple event types
        for block in record.message.get_content_blocks():
            if isinstance(block, ThinkingBlock):
                group_key = None
                if group_by == "event_type":
                    group_key = "thinking"

                yield TimelineEvent(
                    event_type="thinking",
                    timestamp=record.timestamp,
                    message_uuid=record.uuid,
                    summary=_truncate(block.thinking),
                    group_key=group_key,
                )

            elif isinstance(block, TextBlock):
                group_key = None
                if group_by == "event_type":
                    group_key = "text"

                yield TimelineEvent(
                    event_type="text",
                    timestamp=record.timestamp,
                    message_uuid=record.uuid,
                    summary=_truncate(block.text),
                    group_key=group_key,
                )

            elif isinstance(block, ToolUseBlock):
                group_key = None
                if group_by == "tool":
                    group_key = block.name
                elif group_by == "event_type":
                    group_key = "tool_use"

                # Include description for Task tool
                summary = block.name
                if block.name == "Task" and block.description:
                    summary = f"Task: {block.description}"

                yield TimelineEvent(
                    event_type="tool_use",
                    timestamp=record.timestamp,
                    message_uuid=record.uuid,
                    summary=summary,
                    tool_name=block.name,
                    tool_use_id=block.id,
                    group_key=group_key,
                )


def _matches_filter(event: TimelineEvent, filter_: TimelineFilter) -> bool:
    """Check if an event matches the filter criteria."""
    # Time range filter
    if filter_.after and event.timestamp and event.timestamp < filter_.after:
        return False
    if filter_.before and event.timestamp and event.timestamp > filter_.before:
        return False

    # Event type filter
    if filter_.event_types and event.event_type not in filter_.event_types:
        return False

    # Tool name filter
    if filter_.tool_names:
        return event.tool_name is not None and event.tool_name in filter_.tool_names

    return True


def build_timeline(
    records: Iterator[ConversationRecord],
    filter_: TimelineFilter | None = None,
    calculate_durations: bool = True,
) -> list[TimelineEvent]:
    """Build a timeline of events from conversation records.

    Events are extracted from content blocks, filtered, and ordered by timestamp.
    Durations are calculated between consecutive events.

    Args:
        records: Iterator of conversation records
        filter_: Optional filter criteria
        calculate_durations: Whether to calculate durations between events

    Returns:
        List of TimelineEvent objects ordered by timestamp
    """
    if filter_ is None:
        filter_ = TimelineFilter()

    events: list[TimelineEvent] = []

    # Extract all events
    for record in records:
        for event in _extract_events_from_record(record, filter_.group_by):
            if _matches_filter(event, filter_):
                events.append(event)

    # Sort by timestamp (None timestamps go to end)
    events.sort(key=lambda e: (e.timestamp is None, e.timestamp))

    # Calculate durations between consecutive events
    if calculate_durations and len(events) > 1:
        for i in range(len(events) - 1):
            current = events[i]
            next_event = events[i + 1]

            if current.timestamp and next_event.timestamp:
                delta = next_event.timestamp - current.timestamp
                current.duration_ms = int(delta.total_seconds() * 1000)

    # Apply pagination
    start = filter_.offset
    end = filter_.offset + filter_.limit if filter_.limit else None

    return events[start:end]


def get_timeline_summary(events: list[TimelineEvent]) -> TimelineSummary:
    """Calculate summary statistics for a timeline.

    Args:
        events: List of timeline events

    Returns:
        TimelineSummary with aggregate statistics
    """
    summary = TimelineSummary(total_events=len(events))

    if not events:
        return summary

    # Count by type and tool
    for event in events:
        event_type = event.event_type
        summary.events_by_type[event_type] = summary.events_by_type.get(event_type, 0) + 1

        if event.tool_name:
            summary.events_by_tool[event.tool_name] = (
                summary.events_by_tool.get(event.tool_name, 0) + 1
            )

    # Find time range
    timestamps = [e.timestamp for e in events if e.timestamp]
    if timestamps:
        summary.first_timestamp = min(timestamps)
        summary.last_timestamp = max(timestamps)

        # Total duration
        delta = summary.last_timestamp - summary.first_timestamp
        summary.total_duration_ms = int(delta.total_seconds() * 1000)

    return summary


def group_events(
    events: list[TimelineEvent],
) -> dict[str, list[TimelineEvent]]:
    """Group events by their group_key.

    Args:
        events: List of timeline events (with group_key set)

    Returns:
        Dict mapping group keys to lists of events
    """
    groups: dict[str, list[TimelineEvent]] = {}

    for event in events:
        key = event.group_key or "ungrouped"
        if key not in groups:
            groups[key] = []
        groups[key].append(event)

    return groups
