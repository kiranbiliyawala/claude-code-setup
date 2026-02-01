"""
EventIndex - Unified index of all trace events.

Combines events from all trace files, normalizes timestamps,
and provides efficient querying and filtering.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING, Any

from ptrace.models import Event

if TYPE_CHECKING:
    from ptrace.archive import TraceArchive


class EventIndex:
    """
    In-memory index of all events from a trace, sorted by timestamp.

    Combines events from:
    - 0-trace.network (network calls)
    - 0-trace.trace (console, actions, screenshots, logs)
    - test.trace (test steps, errors)

    Provides filtering by event type, time range, and type-specific criteria.
    """

    def __init__(self, archive: TraceArchive):
        """
        Initialize EventIndex by parsing all trace files.

        Args:
            archive: TraceArchive to read events from
        """
        self.archive = archive
        self._events: list[Event] = []
        self._by_type: dict[str, list[Event]] = {}
        self._parsed = False
        self._trace_start_ms: float = 0

    def _ensure_parsed(self) -> None:
        """Parse all events if not already done."""
        if self._parsed:
            return

        from ptrace.parsers import (  # noqa: PLC0415
            BrowserTraceParser,
            NetworkParser,
            TestTraceParser,
        )

        # Get trace start time for normalization
        self._trace_start_ms = self.archive.get_trace_start_time()

        # Parse all sources
        all_events: list[Event] = []

        # Network events
        network_parser = NetworkParser(self.archive)
        for event in network_parser.parse():
            all_events.append(event)

        # Browser trace events (console, actions, screenshots)
        browser_parser = BrowserTraceParser(self.archive)
        for event in browser_parser.parse():
            all_events.append(event)

        # Test trace events (test steps, errors)
        test_parser = TestTraceParser(self.archive)
        for event in test_parser.parse():
            all_events.append(event)

        # Sort by timestamp
        all_events.sort(key=lambda e: (e.timestamp_ms, e.event_type))

        # Re-index after sorting
        for i, event in enumerate(all_events):
            event.index = i

        self._events = all_events

        # Build type index
        self._by_type = {}
        for event in self._events:
            if event.event_type not in self._by_type:
                self._by_type[event.event_type] = []
            self._by_type[event.event_type].append(event)

        self._parsed = True

    def all(self) -> Iterator[Event]:
        """Iterate over all events in timestamp order."""
        self._ensure_parsed()
        yield from self._events

    def count(self) -> int:
        """Get total number of events."""
        self._ensure_parsed()
        return len(self._events)

    def by_type(self, event_type: str) -> Iterator[Event]:
        """
        Get events of a specific type.

        Args:
            event_type: One of: network, console, action, error, screenshot, log, input
        """
        self._ensure_parsed()
        yield from self._by_type.get(event_type, [])

    def count_by_type(self, event_type: str) -> int:
        """Get count of events of a specific type."""
        self._ensure_parsed()
        return len(self._by_type.get(event_type, []))

    def in_range(self, start_ms: float, end_ms: float) -> Iterator[Event]:
        """
        Get events within a time range.

        Args:
            start_ms: Start timestamp (ms from trace start)
            end_ms: End timestamp (ms from trace start)
        """
        self._ensure_parsed()
        for event in self._events:
            if start_ms <= event.timestamp_ms <= end_ms:
                yield event
            elif event.timestamp_ms > end_ms:
                # Events are sorted, can stop early
                break

    def after(self, timestamp_ms: float) -> Iterator[Event]:
        """Get events after a timestamp."""
        self._ensure_parsed()
        for event in self._events:
            if event.timestamp_ms >= timestamp_ms:
                yield event

    def before(self, timestamp_ms: float) -> Iterator[Event]:
        """Get events before a timestamp."""
        self._ensure_parsed()
        for event in self._events:
            if event.timestamp_ms <= timestamp_ms:
                yield event
            else:
                break

    def get_by_index(self, index: int) -> Event | None:
        """Get event by its index."""
        self._ensure_parsed()
        if 0 <= index < len(self._events):
            return self._events[index]
        return None

    def network(self) -> Iterator[Event]:
        """Get all network events."""
        return self.by_type("network")

    def console(self) -> Iterator[Event]:
        """Get all console events."""
        return self.by_type("console")

    def actions(self) -> Iterator[Event]:
        """Get all action events."""
        return self.by_type("action")

    def errors(self) -> Iterator[Event]:
        """Get all error events."""
        return self.by_type("error")

    def screenshots(self) -> Iterator[Event]:
        """Get all screenshot events."""
        return self.by_type("screenshot")

    def has_errors(self) -> bool:
        """Check if the trace contains any errors."""
        self._ensure_parsed()
        return len(self._by_type.get("error", [])) > 0

    def get_summary(self) -> dict[str, Any]:
        """
        Get summary statistics for the trace.

        Returns:
            Dictionary with counts per event type and metadata
        """
        self._ensure_parsed()

        # Calculate duration
        if self._events:
            # Filter out inf timestamps (errors without timestamps)
            finite_events = [e for e in self._events if e.timestamp_ms != float("inf")]
            if finite_events:
                duration_ms = finite_events[-1].timestamp_ms - finite_events[0].timestamp_ms
            else:
                duration_ms = 0
        else:
            duration_ms = 0

        return {
            "total_events": len(self._events),
            "duration_ms": duration_ms,
            "event_counts": {
                event_type: len(events) for event_type, events in self._by_type.items()
            },
            "has_errors": self.has_errors(),
            "test_name": self.archive.get_test_name(),
            "browser": self.archive.get_browser_name(),
            "viewport": self.archive.get_viewport(),
        }

    def correlate(
        self,
        timestamp_ms: float,
        window_ms: float = 500,
    ) -> dict[str, list[dict[str, Any]]]:
        """
        Find all events within a time window around a timestamp.

        Events are grouped by type and sorted by distance from the target timestamp.

        Args:
            timestamp_ms: Center timestamp
            window_ms: Window size (±window_ms from center)

        Returns:
            Dictionary with events grouped by type, each with distance_ms field
        """
        self._ensure_parsed()

        start = timestamp_ms - window_ms
        end = timestamp_ms + window_ms

        result: dict[str, list[dict[str, Any]]] = {
            "network": [],
            "console": [],
            "action": [],
            "error": [],
            "screenshot": [],
            "log": [],
        }

        for event in self.in_range(start, end):
            event_dict = event.to_dict()
            event_dict["distance_ms"] = abs(event.timestamp_ms - timestamp_ms)
            if event.event_type in result:
                result[event.event_type].append(event_dict)

        # Sort each group by distance
        for events in result.values():
            events.sort(key=lambda e: e["distance_ms"])

        return result

    def closest_screenshot(self, timestamp_ms: float) -> Event | None:
        """
        Find the screenshot closest to a given timestamp.

        Args:
            timestamp_ms: Target timestamp

        Returns:
            The screenshot event closest to the timestamp, or None if no screenshots
        """
        self._ensure_parsed()

        screenshots = list(self.screenshots())
        if not screenshots:
            return None

        return min(screenshots, key=lambda e: abs(e.timestamp_ms - timestamp_ms))
