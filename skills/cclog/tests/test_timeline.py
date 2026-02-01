"""Tests for the timeline module."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from cclog.parser import parse_jsonl
from cclog.timeline import (
    TimelineEvent,
    TimelineFilter,
    build_timeline,
    get_timeline_summary,
    group_events,
)


class TestTimelineEvent:
    """Tests for TimelineEvent dataclass."""

    def test_to_dict(self) -> None:
        """Test event to dict conversion."""
        event = TimelineEvent(
            event_type="tool_use",
            timestamp=datetime(2025, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
            message_uuid="msg-001",
            summary="Read file",
            tool_name="Read",
            tool_use_id="tool-001",
        )
        result = event.to_dict()

        assert result["event_type"] == "tool_use"
        assert result["tool_name"] == "Read"
        assert result["tool_use_id"] == "tool-001"
        assert "2025-01-01" in result["timestamp"]

    def test_to_dict_optional_fields(self) -> None:
        """Test that optional fields are excluded when not set."""
        event = TimelineEvent(
            event_type="text",
            timestamp=None,
            message_uuid="msg-001",
            summary="Hello",
        )
        result = event.to_dict()

        assert "tool_name" not in result
        assert "duration_ms" not in result
        assert result["timestamp"] is None


class TestTimelineFilter:
    """Tests for TimelineFilter dataclass."""

    def test_default_values(self) -> None:
        """Test default filter values."""
        filter_ = TimelineFilter()
        assert filter_.after is None
        assert filter_.before is None
        assert filter_.event_types is None
        assert filter_.tool_names is None
        assert filter_.group_by is None
        assert filter_.limit is None
        assert filter_.offset == 0


class TestBuildTimeline:
    """Tests for build_timeline function."""

    def test_build_timeline_basic(self, temp_jsonl_file: Path) -> None:
        """Test basic timeline building."""
        records = parse_jsonl(temp_jsonl_file)
        events = build_timeline(records)

        assert len(events) > 0
        # Events should include user_message, text, tool_use, tool_result
        event_types = {e.event_type for e in events}
        assert "user_message" in event_types
        assert "tool_use" in event_types

    def test_build_timeline_with_duration(self, temp_jsonl_file: Path) -> None:
        """Test timeline with duration calculation."""
        records = parse_jsonl(temp_jsonl_file)
        events = build_timeline(records, calculate_durations=True)

        # At least some events should have duration calculated
        events_with_duration = [e for e in events if e.duration_ms is not None]
        assert len(events_with_duration) > 0

    def test_build_timeline_filter_event_type(self, temp_jsonl_file: Path) -> None:
        """Test filtering by event type."""
        records = parse_jsonl(temp_jsonl_file)
        filter_ = TimelineFilter(event_types=["tool_use"])
        events = build_timeline(records, filter_)

        for event in events:
            assert event.event_type == "tool_use"

    def test_build_timeline_filter_tool_name(self, temp_jsonl_file: Path) -> None:
        """Test filtering by tool name."""
        records = parse_jsonl(temp_jsonl_file)
        filter_ = TimelineFilter(tool_names=["Read"])
        events = build_timeline(records, filter_)

        for event in events:
            assert event.tool_name == "Read"

    def test_build_timeline_pagination(self, temp_jsonl_file: Path) -> None:
        """Test timeline pagination."""
        records = parse_jsonl(temp_jsonl_file)
        all_events = build_timeline(records)

        # Get first 2 events
        records = parse_jsonl(temp_jsonl_file)
        filter_ = TimelineFilter(limit=2, offset=0)
        first_page = build_timeline(records, filter_)

        assert len(first_page) == min(2, len(all_events))

        # Get next 2 events
        records = parse_jsonl(temp_jsonl_file)
        filter_ = TimelineFilter(limit=2, offset=2)
        second_page = build_timeline(records, filter_)

        # Pages should be different (if there are enough events)
        if len(all_events) > 2:
            assert first_page != second_page

    def test_build_timeline_group_by_tool(self, temp_jsonl_file: Path) -> None:
        """Test grouping by tool."""
        records = parse_jsonl(temp_jsonl_file)
        filter_ = TimelineFilter(group_by="tool")
        events = build_timeline(records, filter_)

        # Tool use events should have group_key set to tool name
        tool_events = [e for e in events if e.event_type == "tool_use"]
        for event in tool_events:
            assert event.group_key == event.tool_name


class TestTimelineSummary:
    """Tests for timeline summary functions."""

    def test_get_timeline_summary(self, temp_jsonl_file: Path) -> None:
        """Test summary calculation."""
        records = parse_jsonl(temp_jsonl_file)
        events = build_timeline(records)
        summary = get_timeline_summary(events)

        assert summary.total_events == len(events)
        assert len(summary.events_by_type) > 0

    def test_get_timeline_summary_empty(self) -> None:
        """Test summary with empty events."""
        summary = get_timeline_summary([])
        assert summary.total_events == 0
        assert summary.total_duration_ms is None

    def test_summary_to_dict(self, temp_jsonl_file: Path) -> None:
        """Test summary to dict conversion."""
        records = parse_jsonl(temp_jsonl_file)
        events = build_timeline(records)
        summary = get_timeline_summary(events)
        result = summary.to_dict()

        assert "total_events" in result
        assert "events_by_type" in result
        assert "events_by_tool" in result


class TestGroupEvents:
    """Tests for group_events function."""

    def test_group_events(self, temp_jsonl_file: Path) -> None:
        """Test event grouping."""
        records = parse_jsonl(temp_jsonl_file)
        filter_ = TimelineFilter(group_by="event_type")
        events = build_timeline(records, filter_)
        groups = group_events(events)

        # Should have multiple groups
        assert len(groups) > 0

    def test_group_events_ungrouped(self, temp_jsonl_file: Path) -> None:
        """Test events without group_key."""
        records = parse_jsonl(temp_jsonl_file)
        events = build_timeline(records)  # No group_by
        groups = group_events(events)

        # All events should be in "ungrouped"
        assert "ungrouped" in groups
